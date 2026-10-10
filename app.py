from datetime import date
import time
import streamlit as st
from polisdiff.extraction import PDFError, render_page
from polisdiff.runtime import web_retriever
from polisdiff.service import analyze_pdf, BusyError
from polisdiff.export import add_review, html_report
from polisdiff.engine import load_catalogue
from polisdiff.session import input_identity, invalidate_result, select_evidence
from polisdiff.presentation import (STATUS_LABELS, STATUS_ICONS, REVIEW_LABELS, SECTION_LABELS,
    MODE_LABELS, SCOPES, STANDARD_LIMITATIONS, summary, counts, observation, expected, next_step, period, explanation)
from polisdiff.models import Status

st.set_page_config(page_title="PolisDiff AI · Проверка ОСАГО", page_icon="🔎", layout="wide")
st.markdown("""<style>
.block-container{max-width:1200px;padding-top:4rem;padding-bottom:3rem}
h1{letter-spacing:-.045em}h2,h3{letter-spacing:-.02em}
[data-testid=stMetric]{border:1px solid #dce5ea;background:white;border-radius:12px;padding:14px}
[data-testid=stMetricLabel]{white-space:normal!important}[data-testid=stMetricLabel] p{white-space:normal!important}
[data-testid=stSidebar]{border-right:1px solid #dce5ea}
[data-testid=stCode] pre{white-space:pre-wrap!important;overflow-wrap:anywhere!important;word-break:break-word}
.stMarkdown p,.stCaption{overflow-wrap:anywhere}.stButton button:focus-visible,a:focus-visible{outline:3px solid #007f73;outline-offset:3px}
[data-testid=stCaptionContainer],[data-testid=stCaptionContainer] p{color:#475569}
[data-testid=stCaptionContainer]{opacity:1}
@media(max-width:640px){.block-container{padding:4rem 1rem 1rem}h1{font-size:2rem}[data-testid=stMetric]{padding:10px}}
</style>""", unsafe_allow_html=True)

catalogue, rules, _ = load_catalogue()
upload_generation = st.session_state.get("upload_generation", 0)
with st.sidebar:
    st.markdown("### PolisDiff AI")
    st.caption("Предварительная проверка ОСАГО · Узбекистан")
    st.divider()
    st.write("Три условия: общая сумма, срок выплаты и уведомление о решении.")
    st.caption("Не юридическое заключение. Интерпретации ожидают проверки юристом: PENDING_LEGAL_REVIEW.")
    st.divider()
    st.caption("Анализ выполняется локально, без внешних AI API. PDF и аннотации хранятся в памяти сессии. Экспортируйте записи перед очисткой.")
    if st.button("Очистить сессию", width="stretch"):
        for key in list(st.session_state):
            del st.session_state[key]
        st.session_state.upload_generation = upload_generation + 1
        st.rerun()

st.caption("POLISDIFF AI / ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА")
st.title("Условия полиса, с доказательствами")
st.write("Найдите три ключевых условия ОСАГО, сравните их с критериями для выбранной даты и проверьте цитаты в оригинале.")
st.info("Результат относится к отдельным условиям, а не ко всему договору. «Не найдено» не означает нарушение.")

with st.container(border=True):
    st.subheader("1. Документ и даты")
    upload_col, date_col = st.columns([1.2, 1])
    with upload_col:
        upload = st.file_uploader("Загрузить PDF ОСАГО", type=["pdf"], key=f"pdf_upload_{upload_generation}")
        st.caption("Текстовый PDF · до 10 МиБ · от 1 до 80 страниц. Русский, узбекская латиница и кириллица. Сканы без текстового слоя не поддерживаются: OCR отсутствует.")
        st.caption("Продукт ОСАГО выбран пользователем. Другие виды страхования не проверяются.")
    with date_col:
        st.write("**Когда применялся договор?**")
        st.caption("Дата применимости — дата, для которой проверяются условия договора и редакция нормы. Установите ее по договору или оферте; дата загрузки и дата, найденная на странице, ее не заменяют.")
        known_date = st.checkbox("Я подтверждаю дату применимости договора", value=False, key=f"known_date_{upload_generation}")
        applicable_input = st.date_input("Дата применимости договора", value=None, disabled=not known_date, key=f"applicable_input_{upload_generation}")
        applicable_date = applicable_input if known_date else None
        audit_date = st.date_input("Дата аудита", value=date.today(), max_value=date.today(), key=f"audit_date_{upload_generation}")
        st.caption("Дата аудита — когда выполняется проверка. Она не определяет, какая редакция нормы применима к договору.")
    if applicable_date is None:
        st.warning("Дата договора неизвестна или не указана. Можно найти связанный текст, но все три числовые проверки останутся без вывода о соответствии.")
    elif applicable_date > audit_date or not date.fromisoformat(catalogue["supported_date_range"][0]) <= applicable_date <= date.fromisoformat(catalogue["supported_date_range"][1]):
        st.warning("Дата вне подтвержденного диапазона каталога или позже даты аудита. Система воздержится от сравнения; проверьте даты и редакцию нормы.")
    with st.expander("Дополнительные настройки поиска"):
        mode_label = st.radio("Поиск доказательств", ["AI + лексический поиск", "AI поиск", "Лексический поиск"], key=f"mode_label_{upload_generation}")
        st.caption("По умолчанию — локальная модель вместе с поиском по словам. Малый тестовый набор не устанавливает преимущество AI в точности. При отсутствии модели используется явно обозначенный поиск по словам.")
    mode = {"AI + лексический поиск": "hybrid", "AI поиск": "semantic", "Лексический поиск": "lexical"}[mode_label]
    analyze = st.button("Анализировать документ", type="primary", disabled=upload is None, width="stretch")

data = upload.getvalue() if upload is not None else None
fingerprint = input_identity(data, audit_date, applicable_date, mode) if data is not None else None
invalidate_result(st.session_state, fingerprint)
if analyze and data is not None:
    if time.monotonic() - st.session_state.get("last_analysis", -1000) < 5:
        st.warning("Подождите пять секунд между анализами.")
    else:
        # An unsuccessful rerun must not leave a previous report downloadable.
        invalidate_result(st.session_state, None)
        st.session_state.last_analysis = time.monotonic()
        try:
            with st.status("Подготовка локального поиска…", expanded=True) as progress:
                # Cache the model only; never cache a mutable document retriever.
                retriever = web_retriever(mode)
                stages = {"extraction": "Читаем документ в отдельном процессе",
                    "retrieval": "Ищем относящиеся к проверкам положения",
                    "evaluation": "Проверяем три выбранных условия",
                    "report": "Готовим отчет и ссылки на доказательства"}
                def on_progress(stage):
                    progress.update(label=stages[stage])
                    st.write(stages[stage])
                doc, report = analyze_pdf(data, audit_date, applicable_date, retriever, on_progress=on_progress)
                st.session_state.document = doc
                st.session_state.report = report
                st.session_state.input_fingerprint = fingerprint
                progress.update(label="Проверка завершена", state="complete", expanded=False)
        except PDFError:
            st.error("PDF не удалось прочитать безопасно: проверьте формат, шифрование, размер и число страниц. Это проблема обработки файла, а не вывод об условиях договора.")
        except BusyError:
            st.warning("Сервер сейчас выполняет другой анализ. Повторите запрос после его завершения.")
        except Exception:
            st.error("Обработка не завершена; отчет не создан. Попробуйте поиск по словам или другой текстовый PDF. Это не означает нарушение в договоре.")


def show_page(doc, pdf_data, page_number, selected_id=None):
    page = doc.pages[page_number-1]
    st.caption(f"Страница PDF {page_number} · {SECTION_LABELS.get(page.section, page.section)} · "
               f"{'текст читается' if page.readable else 'текст поврежден или отсутствует'}")
    selected = next((p for p in doc.passages if p.id == selected_id and p.page == page_number), None)
    if selected:
        st.write("**Цитата выбранной находки**")
        st.code(selected.text, language=None, wrap_lines=True)
    left, right = st.columns([1, 1])
    with left:
        try:
            key = (doc.sha256, page_number)
            cached = st.session_state.get("preview")
            if not cached or cached[0] != key:
                cached = (key, render_page(pdf_data, page_number))
                st.session_state.preview = cached
            st.image(cached[1], width="stretch")
        except PDFError:
            st.error("Изображение страницы недоступно. Проверьте оригинальный PDF.")
    with right:
        st.write("**Исходный текст страницы**")
        st.code(page.text or "Текстовый слой отсутствует", language=None, wrap_lines=True)
    st.caption("Цитаты сохранены без перевода. Координаты объединяют блоки текста и недостаточно точны для выделения цитаты; показана правильная страница без ложной подсветки.")


if "report" in st.session_state and upload is not None:
    report, doc = st.session_state.report, st.session_state.document
    review_context = f"{report.document_sha256}_{report.created_at.isoformat()}"
    st.subheader("2. Краткий итог")
    st.write(summary(report))
    st.write(f"**Документ:** {upload.name} · {report.page_count} страниц · {', '.join(report.detected_languages)}")
    st.caption(f"Дата договора: {report.applicable_date or 'не подтверждена'} · дата аудита: {report.audit_date} · проверок: {len(report.findings)}")
    c = counts(report)
    cols = st.columns(4)
    for col, status, label in zip(cols, Status, ["Согласуются с критерием", "Возможные несоответствия", "Не найдены", "Недостаточно данных"]):
        col.metric(label, c[status])
    if report.retrieval_requested != report.retrieval_used:
        st.warning("AI-модель недоступна. Анализ выполнен поиском по словам, без AI. Фактический режим указан в отчете.")
    st.caption("Фактический поиск: " + MODE_LABELS[report.retrieval_used])
    unreadable = [str(p.number) for p in doc.pages if not p.readable]
    if unreadable:
        st.warning("Проблема обработки: текст не читается надежно на страницах " + ", ".join(unreadable) + ". Это ограничение PDF, а не страхового условия.")
    if doc.detected_dates:
        st.caption("Найденные на первой странице даты — только подсказки: " + ", ".join(map(str, doc.detected_dates)))
    st.caption("Только три условия; полнота поиска не гарантируется. Все интерпретации: PENDING_LEGAL_REVIEW.")
    result_tab, evidence_tab, review_tab, source_tab = st.tabs(["Результаты", "Доказательства документа", "Решение аналитика", "Источники и ограничения"])
    with result_tab:
        for f in report.findings:
            with st.container(border=True):
                st.subheader(f.rule_name)
                st.write(f"**{STATUS_ICONS[f.status]} {STATUS_LABELS[f.status]}**")
                st.write("**Что проверяли**")
                st.write(SCOPES.get(f.rule_id, f.check_scope))
                st.write("**Что найдено**")
                st.write(observation(f))
                st.write("**Почему получен результат**")
                st.write(explanation(f))
                st.write("**Ориентир для выбранной даты**")
                st.write(expected(f))
                if f.source_quote:
                    st.code(f.source_quote, language=None, wrap_lines=True)
                st.caption(f"{f.provision_reference} · {period(f)}")
                st.link_button("Официальный источник · LexUZ", f.source_url)
                st.write("**Доказательства**")
                if not f.evidence:
                    st.write("Подходящее доказательство не найдено. Цитата и страница отсутствуют.")
                for i, ev in enumerate(f.evidence):
                    st.caption(f"Страница PDF {ev.page} · {SECTION_LABELS.get(ev.section, ev.section)}")
                    st.code(ev.quote, language=None, wrap_lines=True)
                    st.button(f"Посмотреть доказательство · стр. {ev.page}", key=f"evidence_{f.rule_id}_{i}",
                        on_click=select_evidence, args=(st.session_state, ev.page, ev.passage_id, f.rule_id))
                    if st.session_state.get("evidence_selection") == ev.passage_id and st.session_state.get("evidence_rule") == f.rule_id:
                        with st.expander("Выбранное доказательство в PDF", expanded=True):
                            show_page(doc, data, ev.page, ev.passage_id)
                st.write("**Следующий шаг**")
                st.write(next_step(f))
                for r in (r for r in report.reviews if r.rule_id == f.rule_id):
                    st.caption(f"Аннотация аналитика: {REVIEW_LABELS[r.action]} · {r.timestamp.isoformat()}")
                    st.text(r.rationale)
                with st.expander("Технические детали · " + f.rule_id):
                    st.json(f.model_dump(mode="json"))
                    st.caption("Запрошено: " + MODE_LABELS[report.retrieval_requested] + "; выполнено: " + MODE_LABELS[report.retrieval_used])
        st.subheader("Сохранить отчет")
        st.caption("HTML — читаемый отчет с цитатами и аннотациями. Для PDF откройте HTML и выберите «Печать → Сохранить как PDF». JSON сохраняет исходные статусы и метаданные.")
        export1, export2 = st.columns(2)
        export1.download_button("Скачать JSON отчет", report.model_dump_json(indent=2), "polisdiff-report.json", "application/json", on_click="ignore", width="stretch")
        export2.download_button("Скачать HTML отчет", html_report(report), "polisdiff-report.html", "text/html", on_click="ignore", width="stretch")
    with evidence_tab:
        st.subheader("Исходный документ")
        selected_page = st.number_input("Страница документа", min_value=1, max_value=len(doc.pages), value=None, placeholder="Номер страницы", step=1, key=f"manual_page_{review_context}")
        if st.button("Показать изображение страницы"):
            select_evidence(st.session_state, selected_page or 1, "manual")
            st.rerun()
        if st.session_state.get("evidence_selection"):
            show_page(doc, data, st.session_state.evidence_page, st.session_state.evidence_selection)
    with review_tab:
        st.subheader("Аннотация аналитика")
        st.write("Запись не меняет результат алгоритма и не является юридической сертификацией. Она хранится в этой сессии; экспортируйте ее перед очисткой.")
        with st.form(f"review_form_{review_context}"):
            names = {f.rule_id: f.rule_name for f in report.findings}
            selected_rule = st.selectbox("Проверка", options=list(names), format_func=names.get, key=f"review_rule_{review_context}")
            action = st.selectbox("Действие", ["further_review", "confirm", "dismiss"], format_func=REVIEW_LABELS.get, key=f"review_action_{review_context}")
            rationale = st.text_area("Обоснование", max_chars=2000, key=f"review_rationale_{review_context}")
            if st.form_submit_button("Записать решение"):
                try:
                    add_review(report, selected_rule, action, rationale)
                    st.rerun()
                except ValueError:
                    st.error("Укажите обоснование длиной от 3 до 2000 символов.")
        for r in report.reviews:
            st.caption(f"{names[r.rule_id]} · {REVIEW_LABELS[r.action]} · {r.timestamp.isoformat()}")
            st.text(r.rationale)
    with source_tab:
        st.write(f"Каталог {catalogue['catalogue_version']} · подтвержденный диапазон: {' — '.join(catalogue['supported_date_range'])}")
        for text in STANDARD_LIMITATIONS:
            st.write("• " + text)
        with st.expander("Предупреждения и метаданные анализа"):
            st.json(report.model_dump(mode="json", exclude={"findings", "reviews"}))
        for rule in rules:
            with st.expander(rule.name):
                st.text(rule.interpretation)
                st.caption(rule.reference)
                st.link_button("LexUZ", rule.official_source)
else:
    st.caption("Загрузите документ, установите даты и запустите проверку. При изменении файла, даты или поиска прежний результат и аннотации удаляются из текущей сессии.")
