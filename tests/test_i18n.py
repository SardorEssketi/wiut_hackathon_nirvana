"""Translations change presentation, never the report's analysis or cited evidence."""
import ast
from html import unescape
from itertools import product
from pathlib import Path
import re
import pytest
from polisdiff.export import add_review, html_report
from polisdiff.i18n import LANGUAGES, ROWS, TRANSLATIONS, tr, placeholders, warning_text, recorded_text
from polisdiff.models import Report, Status
from polisdiff.session import preserve_translated_choices, restore_translated_choices
from polisdiff.presentation import (summary, counts, STATUS_LABELS, labels, observation,
    expected, explanation, next_step, rule_name)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def report():
    return Report.model_validate_json((ROOT/'evaluation/reports/lexical/regression_evaluation/ru-Cyrl_match.json').read_bytes())


def test_complete_translation_catalogue_and_same_placeholders():
    assert set(LANGUAGES) == {'ru', 'uz-Latn', 'uz-Cyrl', 'en'}
    assert len(ROWS) == len(TRANSLATIONS['ru'])
    for row in ROWS:
        for text in row:
            assert text.strip() and placeholders(text) == placeholders(row[0])
        assert not re.search('[А-Яа-яЁё]', row[1])
        assert not re.search('[А-Яа-яЁёЎҚҒҲўқғҳ]', row[2])
        assert re.search('[А-Яа-яЁёЎҚҒҲўқғҳ]', row[3]) or not re.search('[А-Яа-яЁёЎҚҒҲўқғҳ]', row[0])


def test_every_fixed_ui_lookup_is_in_catalogue():
    for path in ['app.py', 'polisdiff/export.py', 'polisdiff/presentation.py']:
        for node in ast.walk(ast.parse((ROOT/path).read_text(encoding='utf-8'))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'tr','t','heading'}:
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    assert node.args[0].value in TRANSLATIONS['ru'], (path,node.lineno,node.args[0].value)


@pytest.mark.parametrize('language', LANGUAGES)
@pytest.mark.parametrize('statuses', list(product(Status, repeat=3)))
def test_all_status_summaries_in_every_language(report, language, statuses):
    for f,status in zip(report.findings,statuses):
        f.status = status
    before = report.model_dump_json()
    c = counts(report)
    prefix = tr('Проверено условий: {total}. Возможных несоответствий: {conflicts}; согласуются с критериями: {matches}; не найдены: {missing}; недостаточно данных: {unverifiable}.', language,
        total=3,conflicts=c[Status.POTENTIAL_CONFLICT],matches=c[Status.MATCH_FOUND],missing=c[Status.NOT_FOUND],unverifiable=c[Status.UNVERIFIABLE])
    text = summary(report,language)
    assert text.startswith(prefix)
    if c[Status.UNVERIFIABLE] == 3:
        assert tr('Ни одно условие не удалось надежно проверить. Это не устанавливает нарушение закона.',language) in text
    html = html_report(report,language)
    assert text in unescape(html)
    assert all(label in unescape(html) for status,label in labels(STATUS_LABELS,language).items() if status in statuses)
    assert report.model_dump_json() == before


@pytest.mark.parametrize('language', LANGUAGES)
def test_export_preserves_original_quotations_review_and_json(report,language):
    # A quotation identical to interface copy must still never be translated.
    quote = 'Что найдено\nСуғурта sugʻurta <script>evil()</script> & 80 000 000'
    f = report.findings[0]
    f.evidence[0].quote = quote
    f.status = Status.POTENTIAL_CONFLICT
    f.evidence[0].extracted_value = 62345678
    f.expected_value = 80000000
    add_review(report,f.rule_id,'further_review','Ўзбекча izoh <img src=x onerror=evil()> & English')
    before = report.model_dump_json()
    html = html_report(report,language)
    assert f'<html lang="{language}" dir="ltr">' in html
    assert quote in unescape(html)
    assert f.source_quote in unescape(html) and f.source_version_note in unescape(html)
    assert report.reviews[0].rationale in unescape(html)
    assert '<script>' not in html and '<img ' not in html
    assert '<link ' not in html and '@page{size:A4' in html
    assert '62 345 678' in explanation(f,language) and '80 000 000' in explanation(f,language)
    assert rule_name(f,language) in unescape(html)
    assert report.model_dump_json() == before


@pytest.mark.parametrize('language', LANGUAGES)
@pytest.mark.parametrize('code', ['applicable_date_unknown','unsupported_applicability_date','appendix_only','incorporation_by_reference'])
def test_abstention_no_evidence_dates_and_next_steps(report,language,code):
    f = report.findings[0]
    f.evidence = []
    f.expected_value = None
    f.status = Status.UNVERIFIABLE
    f.uncertainty = [code]
    assert observation(f,language) == tr('Подходящее доказательство не найдено. Числовое значение не установлено.',language)
    assert expected(f,language) == tr('Применимая версия нормы не установлена; ориентир не выбран.',language)
    assert next_step(f,language) in unescape(html_report(report,language))


@pytest.mark.parametrize('language', LANGUAGES)
def test_all_static_engine_reasons_have_real_translations(language):
    tree = ast.parse((ROOT/'polisdiff/engine.py').read_text(encoding='utf-8'))
    dynamic_parts = {id(child) for node in ast.walk(tree) if isinstance(node,ast.JoinedStr) for child in ast.walk(node)}
    reasons = {n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)
               and id(n) not in dynamic_parts and n.value.endswith('.') and re.search('[А-Яа-яЁё]',n.value)}
    for reason in reasons:
        assert reason in TRANSLATIONS[language],reason
    unknown = '<new unrecognized reason>'
    assert unknown in recorded_text(unknown,language)
    assert 'FileNotFoundError' in warning_text('Semantic retrieval unavailable (FileNotFoundError); lexical fallback used.',language)
    assert '7' in warning_text('Page 7: insufficient or damaged text; OCR is not enabled. Manual review required.',language)


def test_unsupported_language_rejected_without_mutating_report(report):
    before = report.model_dump_json()
    with pytest.raises(KeyError):
        html_report(report,'unsupported')
    assert report.model_dump_json() == before


def test_language_callback_preserves_option_ids_without_copying_document_state(report):
    state={'report':report,'document':object(),'mode_label_0':'lexical',
        'review_rule_example':'OSAGO_PAYMENT','review_action_example':'confirm','ui_language':'en'}
    preserve_translated_choices(state)
    assert set(state['_translated_choices']) == {'mode_label_0','review_rule_example','review_action_example'}
    state['mode_label_0']='hybrid'
    state['review_action_example']='further_review'
    restore_translated_choices(state)
    assert state['mode_label_0']=='lexical' and state['review_action_example']=='confirm'
    assert state['report'] is report and state['ui_language']=='en' and '_translated_choices' not in state
