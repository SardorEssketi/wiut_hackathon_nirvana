from datetime import date
from html import unescape
from pathlib import Path
import hashlib
import subprocess
import pytest
from streamlit.testing.v1 import AppTest
from polisdiff.deployment import model_files_status, deployment_diagnostics, source_revision
from polisdiff.export import html_report
from polisdiff.i18n import LANGUAGES, tr
from polisdiff.models import Report, Status
from polisdiff.presentation import compact_finding, pending_date, readiness_message

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def unknown():
    return Report.model_validate_json((ROOT/'evaluation/reports/lexical/regression_evaluation/ru-Cyrl_unknown_date.json').read_bytes())


@pytest.mark.parametrize('language', LANGUAGES)
def test_pending_index_and_shared_blocker_preserve_report(unknown, language):
    before = unknown.model_dump_json()
    assert unknown.applicable_date is None
    html = html_report(unknown, language)
    assert unescape(html).count(readiness_message(language)) == 1
    assert html.count('<details class="pending">') == 3
    for f in unknown.findings:
        row = compact_finding(unknown, f, language)
        assert row['pending'] and f.status == Status.UNVERIFIABLE
        assert f.expected_value is None and not f.source_quote
        assert row['observation'] in unescape(html)
        assert '80 000 000' not in row['observation']
        for ev in f.evidence:
            assert ev.quote in unescape(html)
            assert str(ev.page) in row['pages']
    assert unknown.model_dump_json() == before


@pytest.mark.parametrize('blocker', ['unsupported_applicability_date', 'unreadable_pages', 'appendix_only'])
def test_other_blockers_not_grouped_as_missing_date(unknown, blocker):
    f = unknown.findings[0]
    f.uncertainty = [blocker]
    assert not pending_date(unknown, f)
    assert not compact_finding(unknown, f)['pending']


def test_confirmed_date_not_pending_and_empty_evidence_has_no_page(unknown):
    unknown.applicable_date = date(2026, 3, 19)
    f = unknown.findings[0]
    assert not pending_date(unknown, f)
    f.evidence = []
    assert compact_finding(unknown, f)['pages'] == ''


def test_preflight_missing_model_does_not_import_or_download_ai(tmp_path, monkeypatch):
    monkeypatch.setenv('POLISDIFF_MODEL_PATH', str(tmp_path))
    def forbidden(*args, **kwargs):
        pytest.fail('Preflight must not spawn a model download')
    monkeypatch.setattr(subprocess, 'run', forbidden)
    result = model_files_status()
    assert result['state'] == 'not_provisioned'
    assert result['bytes'] == 0 and len(result['missing']) == 5
    (tmp_path/'config.json').write_text('{}')
    assert model_files_status()['state'] == 'not_provisioned'


def test_files_present_not_a_claim_of_loaded_ai(tmp_path, monkeypatch):
    monkeypatch.setenv('POLISDIFF_MODEL_PATH', str(tmp_path))
    for name in ['config.json','model.safetensors','tokenizer.json','modules.json','1_Pooling/config.json']:
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'placeholder')
    assert model_files_status()['state'] == 'files_present'
    assert model_files_status()['bytes'] == 55


def test_diagnostics_have_revision_dependencies_and_content_identity():
    result = deployment_diagnostics()
    assert len(result['source_content_sha256']) == 64
    assert result['dependencies']['streamlit']
    assert result['offline']['HF_HUB_OFFLINE'] == '1'
    assert 'pdf' not in result and 'secrets' not in result


def test_revision_timeout_safe(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs['timeout'])
    monkeypatch.setattr(subprocess, 'run', timeout)
    source_revision.cache_clear()
    try:
        assert source_revision() is None
    finally:
        source_revision.cache_clear()


@pytest.mark.parametrize('language', LANGUAGES)
def test_readiness_unknown_once_before_analysis_and_no_inferred_date(language, monkeypatch, tmp_path):
    monkeypatch.setenv('POLISDIFF_MODEL_PATH', str(tmp_path))
    app = AppTest.from_file(str(ROOT/'app.py'))
    app.session_state['ui_language'] = language
    app.run(timeout=30)
    assert not app.exception
    assert [w.value for w in app.warning].count(readiness_message(language)) == 1
    assert app.session_state['applicable_input_0'] is None
    assert app.session_state['known_date_0'] is False
    assert any('AI' in w.value for w in app.warning if w.value != readiness_message(language))
    assert 'report' not in app.session_state
