from datetime import date
import hashlib
import time
import streamlit as st
from polisdiff.extraction import PDFError, render_page
from polisdiff.retrieval import Retriever
from polisdiff.service import analyze_pdf, BusyError
from polisdiff.export import add_review, html_report
from polisdiff.engine import load_catalogue

st.set_page_config(page_title="PolisDiff AI · Аудит ОСАГО", page_icon="🔎", layout="wide")
st.markdown("""<style>
.block-container{max-width:1260px;padding-top:2rem}
h1{letter-spacing:-.04em} [data-testid=stMetric]{background:white;border:1px solid #dfe6ed;border-radius:12px;padding:16px}
[data-testid=stSidebar]{border-right:1px solid #dfe6ed}
.eyebrow{font-size:12px;letter-spacing:.16em;color:#007f73;font-weight:700}
.hero{padding:24px 0 12px}.muted{color:#536579}
</style>""", unsafe_allow_html=True)


@st.cache_resource
def get_retriever(mode):
    return Retriever(mode=mode)


with st.sidebar:
    st.markdown("### PolisDiff AI")
    st.caption("Контроль условий страхования · Узбекистан")
    st.divider()
    st.markdown("**Область проверки**")
    st.write("ОСАГО: три числовых условия и точные ссылки на доказательства.")
    st.markdown("**Правовая проверка**")
    st.code("PENDING_LEGAL_REVIEW", language=None)
    st.caption("Интерпретации инженера ожидают проверки юристом.")
    st.divider()
    st.caption("Текст и PDF остаются в памяти этой сессии. Внешние AI API не используются. Используйте публичные или синтетические документы.")
    if st.button("Очистить сессию", use_container_width=True):
        for key in list(st.session_state):
            del st.session_state[key]
        st.rerun()

st.markdown('<div class="hero"><div class="eyebrow">EVIDENCE • LANGUAGE • DATE</div><h1>Условия полиса, с доказательствами</h1><p class="muted">Проверка публичной оферты ОСАГО на русском и узбекском — латиница и кириллица.</p></div>', unsafe_allow_html=True)
st.info("Результаты помогают аналитику проверить документ. Они не являются юридическим заключением. «Не найдено» не означает нарушение.")

with st.container(border=True):
    st.subheader("1. Документ и даты")
    upload_col, date_col = st.columns([1.4, 1])
    with upload_col:
        upload = st.file_uploader("Загрузить PDF ОСАГО", type=["pdf"], help="До 10 МиБ, 80 страниц. Только PDF с текстовым слоем; OCR не включен.")
        st.caption("ОСАГО — продукт выбран пользователем. Другие страховые продукты не поддерживаются.")
    with date_col:
        audit_date = st.date_input("Дата аудита", value=date.today(), max_value=date.today())
        known_date = st.checkbox("Я подтверждаю дату применимости договора", value=False,
            help="Для исторической оферты укажите ее применимую дату. При переходе между редакциями требуется юрист.")
        applicable_input = st.date_input("Дата применимости договора", value=date(2026, 1, 5), disabled=not known_date,
            max_value=audit_date)
        applicable_date = applicable_input if known_date else None
    mode_label = st.radio("Поиск доказательств", ["AI + лексический поиск", "AI поиск", "Лексический поиск"], horizontal=True)
    mode = {"AI + лексический поиск": "hybrid", "AI поиск": "semantic", "Лексический поиск": "lexical"}[mode_label]
    analyze = st.button("Анализировать документ", type="primary", disabled=upload is None, use_container_width=True)

if upload is not None:
    data = upload.getvalue()
    fingerprint = (hashlib.sha256(data).hexdigest(), str(audit_date), str(applicable_date), mode)
    if "input_fingerprint" in st.session_state and st.session_state.input_fingerprint != fingerprint:
        st.session_state.pop("report", None)
        st.session_state.pop("document", None)
    if analyze:
        if time.monotonic() - st.session_state.get("last_analysis", -1000) < 5:
            st.warning("Подождите пять секунд между анализами.")
        else:
            st.session_state.last_analysis = time.monotonic()
            try:
                with st.status("Обработка документа…", expanded=True) as progress:
                    st.write("Загрузка локальной модели и безопасное извлечение PDF")
                    retriever = get_retriever(mode)
                    doc, report = analyze_pdf(data, audit_date, applicable_date, retriever)
                    st.session_state.document = doc
                    st.session_state.report = report
                    st.session_state.input_fingerprint = fingerprint
                    progress.update(label="Анализ завершен", state="complete", expanded=False)
            except (PDFError, BusyError, ValueError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("Обработка не завершена. Результат не создан; попробуйте лексический поиск или другой поддерживаемый PDF.")

if "report" in st.session_state and upload is not None:
    report = st.session_state.report
    doc = st.session_state.document
    result_tab, evidence_tab, review_tab, source_tab = st.tabs(["Результаты", "Доказательства документа", "Решение аналитика", "Источники и ограничения"])
    with result_tab:
        st.subheader("2. Результаты трех проверок")
        labels = {"MATCH_FOUND": "Условие найдено", "POTENTIAL_CONFLICT": "Возможное противоречие", "NOT_FOUND": "Не найдено", "UNVERIFIABLE": "Не проверяется"}
        cols = st.columns(4)
        for col, (status, label) in zip(cols, labels.items()):
            col.metric(label, sum(f.status.value == status for f in report.findings))
        st.caption(f"Языки/письменности: {', '.join(doc.languages)} · Страниц: {report.page_count} · Фактический поиск: {report.retrieval_used} · Анализ: {report.timings_seconds['end_to_end']:.2f} с")
        st.caption(f"Инициализация модели: {report.timings_seconds['model_initialization']:.2f} с (при первом запуске отдельно от времени анализа)")
        if doc.detected_dates:
            st.caption("Даты на первой странице (подсказки, не автоматически выбранная дата договора): " + ", ".join(map(str, doc.detected_dates)))
        for warning in report.warnings:
            st.warning(warning)
        for finding in report.findings:
            with st.expander(f"{labels[finding.status.value]} · {finding.rule_name}", expanded=True):
                st.code(finding.status.value, language=None)
                st.write(finding.reason)
                for ev in finding.evidence:
                    st.caption(f"Страница {ev.page} · {ev.section} · фрагмент {ev.passage_id}")
                    st.code(ev.quote, language=None, wrap_lines=True)
                    if ev.extracted_value is not None:
                        st.caption(f"Извлечено: {ev.extracted_value:g} {ev.unit}")
                st.write(f"[Официальный источник]({finding.source_url})")
                st.caption(f"{finding.provision_reference} · версия с {finding.effective_from} по {finding.effective_to or 'дату верификации 10.10.2026'}")
                if finding.source_quote:
                    st.code(finding.source_quote, language=None)
                st.caption("PENDING_LEGAL_REVIEW · Ручная проверка обязательна")
        export1, export2 = st.columns(2)
        export1.download_button("Скачать JSON отчет", report.model_dump_json(indent=2), "polisdiff-report.json", "application/json", use_container_width=True)
        export2.download_button("Скачать HTML отчет", html_report(report), "polisdiff-report.html", "text/html", use_container_width=True)
    with evidence_tab:
        st.subheader("3. Исходный документ")
        selected_page = st.number_input("Страница документа", min_value=1, max_value=len(doc.pages), value=1, step=1)
        page = doc.pages[selected_page-1]
        st.caption(f"Раздел: {page.section} · читаемый текст: {page.readable} · символов: {page.chars}")
        left, right = st.columns(2)
        with left:
            if st.button("Показать изображение страницы"):
                try:
                    st.image(render_page(data, selected_page), use_container_width=True)
                except PDFError as exc:
                    st.error(str(exc))
        with right:
            st.code(page.text or "Текстовый слой отсутствует", language=None, wrap_lines=True)
        st.caption("Исходные Unicode-символы сохранены. Нормализация используется только для поиска. Координаты и смещения доступны в JSON.")
    with review_tab:
        st.subheader("4. Решение аналитика")
        st.caption("Локальный демонстрационный аналитик. Действия не заменяют правовой проверки и не меняют исходный результат алгоритма.")
        with st.form("review_form"):
            selected_rule = st.selectbox("Проверка", options=[f.rule_id for f in report.findings])
            action_label = st.selectbox("Действие", ["Передать на проверку", "Подтвердить находку", "Отклонить находку"])
            rationale = st.text_area("Обоснование", max_chars=2000)
            submitted = st.form_submit_button("Записать решение")
            if submitted:
                try:
                    action = {"Передать на проверку": "further_review", "Подтвердить находку": "confirm", "Отклонить находку": "dismiss"}[action_label]
                    add_review(report, selected_rule, action, rationale)
                    st.success("Действие записано в сессии; включено в экспорт отчета.")
                except ValueError:
                    st.error("Укажите обоснование длиной не менее трех символов.")
        for action in report.reviews:
            st.write(f"{action.timestamp.isoformat()} · {action.rule_id} · {action.action}")
            st.text(action.rationale)
    with source_tab:
        catalogue, rules, _ = load_catalogue()
        st.write(f"Каталог {catalogue['catalogue_version']} · проверен по первоисточникам {catalogue['verified_access_date']}")
        for rule in rules:
            st.markdown(f"**{rule.name}**")
            st.write(rule.interpretation)
            st.write(f"[LexUZ]({rule.official_source}) · {rule.reference}")
        st.warning("OCR не установлен и не проверен: сканы не поддерживаются. Обнаружение языка и приложений основано на эвристиках. Проверяются только три условия; полнота поиска не гарантируется. Даты до 05.08.2024 и после 10.10.2026 не поддерживаются.")
else:
    st.caption("Загрузите PDF и укажите дату применимости договора. Без подтвержденной даты система воздержится от сравнения с законом.")
