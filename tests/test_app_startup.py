"""App startup across a source update in a long-lived Streamlit process."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import polisdiff.extraction as extraction
import polisdiff.presentation as presentation


APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.mark.parametrize("stale_modules", ["extraction", "presentation", "both", "readiness"])
def test_stale_module_requires_reboot_without_import_traceback(monkeypatch, stale_modules):
    # Python keeps imported modules in sys.modules after files change on disk.
    # Model the previous release's API while running the new app entry point.
    if stale_modules in {"extraction", "both"}:
        monkeypatch.delattr(extraction, "render_evidence")
    if stale_modules in {"presentation", "both"}:
        monkeypatch.delattr(presentation, "finding_details")
    if stale_modules == 'readiness':
        monkeypatch.delattr(presentation, 'compact_finding')
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert len(app.error) == 1
    assert "reboot" in app.error[0].value.lower()
    assert "Manage app" in app.error[0].value
    assert not app.get("file_uploader")


def test_fresh_process_api_starts_app():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert not app.error
    assert len(app.get("file_uploader")) == 1
