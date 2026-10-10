from datetime import date
from itertools import product
from pathlib import Path
from html import unescape
import re
import pytest
from polisdiff.models import Report, Status
from polisdiff.presentation import summary, counts, STATUS_LABELS, observation, next_step, explanation
from polisdiff.export import html_report, add_review, source_link
from polisdiff.session import input_identity, invalidate_result, select_evidence

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def report():
    # Historical JSON remains readable without new optional finding metadata.
    return Report.model_validate_json((ROOT / 'evaluation/reports/lexical/regression_evaluation/ru-Cyrl_match.json').read_bytes())


@pytest.mark.parametrize('statuses', list(product(Status, repeat=3)))
def test_all_summary_status_combinations(report, statuses):
    for f, status in zip(report.findings, statuses):
        f.status = status
    text = summary(report)
    c = counts(report)
    assert 'Проверено условий: 3' in text
    assert f'несоответствий: {c[Status.POTENTIAL_CONFLICT]}' in text
    assert f'критериями: {c[Status.MATCH_FOUND]}' in text
    assert f'не найдены: {c[Status.NOT_FOUND]}' in text
    assert f'недостаточно данных: {c[Status.UNVERIFIABLE]}' in text
    if statuses == (Status.UNVERIFIABLE,) * 3:
        assert 'не устанавливает нарушение' in text
    html = html_report(report)
    assert summary(report) in html
    assert all(STATUS_LABELS[s] in html for s in statuses)


def test_no_evidence_and_date_explanations(report):
    f = report.findings[0]
    f.evidence = []
    f.status = Status.UNVERIFIABLE
    f.expected_value = None
    f.uncertainty = ['applicable_date_unknown']
    report.applicable_date = None
    assert 'не найдено' in observation(f)
    assert 'дату' in next_step(f)
    html = html_report(report)
    assert 'Цитата и страница отсутствуют' in html
    assert 'Не подтверждена' in html
    assert 'Применимая версия нормы не установлена' in html
    f.uncertainty = ['unsupported_applicability_date']
    assert 'редакцией' in next_step(f)


def test_unicode_escaping_export_consistency_and_no_active_links(report):
    attack = '<img src=x onerror="alert(1)"> Суғурта, sugʻurta, русский & <script>evil</script>'
    report.findings[0].evidence[0].quote = attack
    report.findings[0].source_url = 'javascript:alert(1)'
    original = [f.model_dump() for f in report.findings]
    for action in ['confirm', 'dismiss', 'further_review']:
        add_review(report, 'OSAGO_SUM', action, attack)
    html = html_report(report)
    assert '<script>' not in html and '<img' not in html
    assert 'javascript:' not in html
    assert '&lt;script&gt;' in html and 'sugʻurta' in html and 'Суғурта' in html
    assert attack in unescape(html)
    assert [f.model_dump() for f in report.findings] == original
    decoded = Report.model_validate_json(report.model_dump_json())
    assert decoded == report
    assert len(decoded.reviews) == 3
    assert all(r.timestamp.tzinfo for r in report.reviews)
    assert '@page{size:A4' in html and 'break-before:page' in html
    assert 'overflow-wrap:anywhere' in html and '<meta charset="utf-8">' in html
    assert '<script' not in html and '<link ' not in html
    assert html.index('Краткий итог') < html.index('Техническое приложение')


@pytest.mark.parametrize('action,rationale', [('bad', 'valid'), ('confirm', '  '), ('confirm', 'x'*2001)])
def test_invalid_review_is_atomic(report, action, rationale):
    with pytest.raises(ValueError):
        add_review(report, 'OSAGO_SUM', action, rationale)
    assert not report.reviews


@pytest.mark.parametrize('change', ['document', 'audit', 'applicable', 'mode', 'remove'])
def test_input_changes_discard_result_reviews_and_preview(report, change):
    add_review(report, 'OSAGO_SUM', 'confirm', 'checked original')
    values = [b'PDF A', date(2026,10,10), date(2026,1,5), 'hybrid']
    before = input_identity(*values)
    state = {'report':report,'document':object(),'input_fingerprint':before,
             'preview':b'png','evidence_page':2,'review_rationale':'checked original','manual_page':2,
             'last_analysis':123,'known_date':True}
    if change == 'document': values[0] = b'PDF B'
    if change == 'audit': values[1] = date(2026,10,9)
    if change == 'applicable': values[2] = None
    if change == 'mode': values[3] = 'lexical'
    invalidate_result(state, None if change == 'remove' else input_identity(*values))
    assert not any(k in state for k in ['report','document','preview','review_rationale','manual_page'])
    assert state['known_date'] and state['last_analysis'] == 123
    invalidate_result(state, before)  # Re-upload A cannot revive the old review.
    assert 'report' not in state


def test_review_rerun_keeps_result_and_selects_correct_page(report):
    identity = input_identity(b'A', report.audit_date, report.applicable_date, 'hybrid')
    state = {'report':report,'input_fingerprint':identity,'preview':b'old'}
    invalidate_result(state, identity)
    assert state['report'] is report
    ev = report.findings[0].evidence[0]
    select_evidence(state, ev.page, ev.passage_id, report.findings[0].rule_id)
    assert state['evidence_page'] == ev.page and state['evidence_selection'] == ev.passage_id
    assert state['evidence_rule'] == report.findings[0].rule_id
    assert 'preview' not in state


def test_plain_comparison_uses_report_values_without_scientific_notation(report):
    f = report.findings[0]
    f.status = Status.POTENTIAL_CONFLICT
    f.evidence[0].extracted_value = 62345678
    f.expected_value = 80000000
    text = explanation(f)
    assert '62 345 678 сум' in text and '80 000 000 сум' in text
    assert text in html_report(report)


@pytest.mark.parametrize('url', ['javascript:alert(1)','https://lex.uz@evil.test/docs/1',
    'https://[', 'https://lex.uz:9999/docs/1', 'data:text/html,<script>evil</script>'])
def test_untrusted_source_urls_do_not_become_links(url):
    assert '<a ' not in source_link(url)


def test_long_original_unicode_quote_is_not_shortened(report):
    text = 'Суғурта sugʻurta русский < & ' * 200
    report.findings[0].evidence[0].quote = text
    assert text in unescape(html_report(report))
