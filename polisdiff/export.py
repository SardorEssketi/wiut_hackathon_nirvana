"""Escaped, self-contained preliminary review; original JSON schema remains readable."""
from datetime import datetime, timezone
from html import escape
from urllib.parse import urlsplit
from .models import Report, ReviewAction
from .presentation import (STATUS_LABELS, STATUS_ICONS, REVIEW_LABELS, SECTION_LABELS,
    MODE_LABELS, SCOPES, STANDARD_LIMITATIONS, summary, observation, expected, next_step, period, explanation)


def add_review(report: Report, rule_id: str, action: str, rationale: str):
    if rule_id not in {f.rule_id for f in report.findings}:
        raise ValueError("Unknown finding")
    report.reviews.append(ReviewAction(rule_id=rule_id, action=action,
        rationale=rationale.strip(), timestamp=datetime.now(timezone.utc)))


def source_link(url: str) -> str:
    try:
        parsed = urlsplit(url)
        permitted = parsed.scheme == "https" and parsed.hostname == "lex.uz" and not parsed.username and parsed.port in {None,443}
    except ValueError:
        permitted = False
    if permitted:
        return f'<a href="{escape(url, quote=True)}" rel="noreferrer">Официальный источник · LexUZ</a>'
    return "Ссылка не открывается: официальный HTTPS-источник не подтвержден."


CSS = """
@page{size:A4;margin:18mm 16mm}*{box-sizing:border-box}html{color-scheme:light}
body{margin:0;background:#edf2f5;color:#182d40;font:15px/1.65 'Segoe UI',Arial,'DejaVu Sans',sans-serif;overflow-wrap:anywhere}
main{max-width:1000px;margin:32px auto;background:white;padding:48px}
h1{font-size:36px;line-height:1.15;letter-spacing:-.04em;margin:8px 0}h2{font-size:23px;margin:32px 0 12px}
h3{font-size:19px;margin:6px 0 12px}h4{font-size:14px;margin:18px 0 4px;color:#40556b}
p{margin:8px 0}.brand{color:#00685e;font-weight:700;letter-spacing:.1em}.muted{color:#536579}
.notice{padding:16px;border-left:4px solid #007f73;background:#f0f7f6}
.metadata{display:grid;grid-template-columns:1fr 1fr;gap:12px 28px;margin:24px 0}
.metadata dt{font-size:12px;color:#536579}.metadata dd{margin:0}.finding{border-top:2px solid #dbe5eb;margin-top:28px;padding-top:22px}
.badge{font-weight:700;display:inline-block;padding:6px 10px;background:#eef2f6;border-radius:6px}
.MATCH_FOUND{background:#edf7f3;color:#14503c}.POTENTIAL_CONFLICT{background:#fff2df;color:#774300}
.NOT_FOUND{background:#eef3f8;color:#314f70}.UNVERIFIABLE{background:#f1f2f5;color:#445064}
blockquote{margin:10px 0;padding:14px 18px;border-left:3px solid #a9bac8;background:#f7f9fb;white-space:pre-wrap;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px}th,td{padding:10px 8px;border-bottom:1px solid #dbe5eb;text-align:left;vertical-align:top}
th{background:#f3f6f8}thead{display:table-header-group}a{color:#006b60}li{margin:6px 0}.technical{font-size:12px}
.review{border:1px solid #dbe5eb;padding:14px;margin:12px 0;white-space:pre-wrap}
@media(max-width:640px){main{margin:0;padding:20px}.metadata{grid-template-columns:1fr}h1{font-size:28px}table{font-size:11px}th,td{padding:6px 4px}}
@media print{body{background:white;font-size:10.5pt}main{max-width:none;margin:0;padding:0}
h2,h3,h4,.badge{break-after:avoid}tr,.review,.metadata{break-inside:avoid}blockquote{orphans:3;widows:3}
.technical{break-before:page}a{color:inherit}.notice,blockquote,.badge{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
"""


def html_report(report: Report) -> str:
    e = lambda value: escape(str(value), quote=True)
    parts = ['<!doctype html><html lang="ru" dir="ltr"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
        f'<title>PolisDiff AI · Предварительная проверка</title><style>{CSS}</style></head><body><main>',
        '<header><p class="brand">POLISDIFF AI</p><h1>Предварительная проверка страхового документа</h1>',
        '<p class="muted">Preliminary Insurance Document Review</p>',
        '<p class="notice">Не юридическое заключение. Проверка отдельных условий помогает специалисту найти и оценить доказательства.</p>',
        '<dl class="metadata">']
    metadata = [("Создан (UTC)", report.created_at.isoformat()), ("Продукт", report.product),
        ("Дата применимости договора", report.applicable_date or "Не подтверждена"),
        ("Дата аудита", report.audit_date), ("Объем", f"{len(report.findings)} условия ОСАГО; {report.page_count} страниц"),
        ("Идентификатор документа · SHA-256", report.document_sha256)]
    for title, value in metadata:
        parts.append(f'<div><dt>{e(title)}</dt><dd>{e(value)}</dd></div>')
    parts += ['</dl></header><section><h2>Краткий итог</h2>', f'<p>{e(summary(report))}</p>',
        '<p class="muted">Все находки требуют ручной проверки контекста. Совпадение не означает одобрение договора.</p></section>',
        '<section><h2>Обзор находок</h2><table><thead><tr><th>Проверка</th><th>Результат</th><th>Наблюдение</th><th>Страница PDF</th><th>Ручная проверка</th></tr></thead><tbody>']
    for f in report.findings:
        pages = ", ".join(str(p) for p in sorted({ev.page for ev in f.evidence})) or "Нет доказательства"
        parts.append(f'<tr><td>{e(f.rule_name)}</td><td>{e(STATUS_ICONS[f.status])} {e(STATUS_LABELS[f.status])}</td>'
            f'<td>{e(observation(f))}</td><td>{e(pages)}</td><td>{"Да" if f.manual_review_required else "Не запрошена"}</td></tr>')
    parts += ['</tbody></table></section><section><h2>Подробные результаты</h2>']
    for f in report.findings:
        parts += [f'<article class="finding" id="{e(f.rule_id)}"><h3>{e(f.rule_name)}</h3>',
            f'<p class="badge {f.status.value}">{e(STATUS_ICONS[f.status])} {e(STATUS_LABELS[f.status])}</p>',
            f'<h4>Что проверяли</h4><p>{e(SCOPES.get(f.rule_id, f.check_scope or f.rule_name))}</p>',
            f'<h4>Что найдено</h4><p>{e(observation(f))}</p>',
            f'<h4>Ориентир для выбранной даты</h4><p>{e(expected(f))}</p>',
            f'<h4>Почему получен результат</h4><p>{e(explanation(f))}</p><h4>Доказательства из документа</h4>']
        if not f.evidence:
            parts.append('<p>Подходящее доказательство не найдено. Цитата и страница отсутствуют.</p>')
        for ev in f.evidence:
            parts.append(f'<p><strong>Страница PDF {ev.page}</strong> · {e(SECTION_LABELS.get(ev.section, ev.section))}</p>'
                         f'<blockquote dir="auto">{e(ev.quote)}</blockquote>')
        parts += [f'<h4>Официальный текст и редакция</h4><p>{e(f.provision_reference)}</p>',
                  f'<p>{source_link(f.source_url)}</p><p>{e(period(f))}</p>']
        parts.append(f'<blockquote dir="auto">{e(f.source_quote)}</blockquote>' if f.source_quote else
                     '<p>Цитата применимой версии не выбрана. Не используйте текущий текст как основание для неизвестной даты.</p>')
        if f.source_version_note:
            parts.append(f'<p>{e(f.source_version_note)}</p>')
        parts += [f'<h4>Неопределенность</h4><p>{e("; ".join(f.uncertainty) or "Отдельные причины не зарегистрированы; правовая интерпретация все равно требует проверки.")}</p>',
            f'<p>{e(f.reviewer_status)}</p><h4>Следующий шаг</h4><p>{e(next_step(f))}</p>']
        for r in (r for r in report.reviews if r.rule_id == f.rule_id):
            parts.append(f'<p class="review">Аннотация: {e(REVIEW_LABELS[r.action])} · {e(r.timestamp.isoformat())}\n{e(r.rationale)}</p>')
        parts.append('</article>')
    parts += ['</section><section><h2>Ограничения и правовая проверка</h2><ul>']
    parts += [f'<li>{e(text)}</li>' for text in STANDARD_LIMITATIONS]
    parts += ['</ul><h3>Ограничения этого анализа</h3><ul>']
    parts += [f'<li>{e(w)}</li>' for w in report.warnings]
    parts += [f'</ul><p>{e(report.disclaimer)}</p></section>',
        '<section><h2>Записи аналитика</h2><p>Аннотации локального аналитика не являются правовой сертификацией. Исходные результаты сохранены. Записи живут в сессии, пока не экспортированы.</p>']
    if not report.reviews:
        parts.append('<p>Аннотации отсутствуют.</p>')
    for r in report.reviews:
        parts.append(f'<div class="review"><strong>{e(REVIEW_LABELS[r.action])}</strong> · {e(r.rule_id)}\n'
                     f'{e(r.timestamp.isoformat())} · {e(r.actor)}\n{e(r.rationale)}</div>')
    parts += ['</section><section class="technical"><h2>Техническое приложение</h2>']
    technical = [("Схема / приложение", f"{report.schema_version} / {report.application_version}"),
        ("SHA-256 документа", report.document_sha256), ("Версия каталога", report.rules_catalogue_version),
        ("SHA-256 каталога", report.rules_catalogue_sha256), ("Основание даты", report.date_basis),
        ("Запрошенный поиск", MODE_LABELS.get(report.retrieval_requested, report.retrieval_requested)),
        ("Фактический поиск", MODE_LABELS.get(report.retrieval_used, report.retrieval_used)),
        ("Отбор фрагментов", report.candidate_selection),
        ("Ревизия модели", report.model_revision or "Не подтверждена / модель не использовалась"),
        ("Языки / письменности", ", ".join(report.detected_languages))]
    parts += [f'<p><strong>{e(name)}:</strong> {e(value)}</p>' for name, value in technical]
    parts += ['<h3>Время обработки, секунд</h3>']
    parts += [f'<p>{e(name)}: {value:.4f}</p>' for name, value in report.timings_seconds.items()]
    parts += ['<h3>Идентификаторы доказательств</h3>']
    for f in report.findings:
        for ev in f.evidence:
            parts.append(f'<p>{e(f.rule_id)} · {e(ev.passage_id)} · PDF {ev.page} · смещение [{ev.start}, {ev.end}) · '
                         f'bbox {e(ev.bbox)} · {e(ev.section)} · значение {e(ev.extracted_value)} {e(ev.unit)}</p>')
    parts += ['<p>Координаты — объединение блоков текста, не точная геометрия цитаты. Визуальное выделение не выполнялось.</p><h3>Предупреждения</h3><ul>']
    parts += [f'<li>{e(w)}</li>' for w in report.warnings]
    parts += ['</ul></section><footer><p class="muted">PolisDiff AI · Печать → Сохранить как PDF. Оригинальные цитаты не переводились.</p></footer></main></body></html>']
    return "".join(parts)
