"""Required integration checks: actual locally provisioned E5 model, with network blocked."""
from datetime import date
from pathlib import Path
import socket
import pytest
from polisdiff.retrieval import Retriever
from polisdiff.service import analyze_pdf

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope="module")
def offline_model():
    original = socket.socket.connect
    def deny_network(*args, **kwargs):
        raise AssertionError("Model initialization attempted network access")
    socket.socket.connect = deny_network
    try:
        retriever = Retriever("hybrid")
        assert retriever.model is not None, retriever.warning
        assert retriever.used == "hybrid"
        yield retriever
    finally:
        socket.socket.connect = original

@pytest.mark.parametrize("language", ["uz-Latn", "uz-Cyrl", "ru-Cyrl"])
def test_actual_offline_semantic_pipeline(offline_model, language):
    doc, report = analyze_pdf((ROOT / f"tests/fixtures/evaluation/{language}_sum_conflict.pdf").read_bytes(),
        date(2026,10,10), date(2026,1,5), offline_model)
    assert report.retrieval_used == "hybrid"
    assert [f.status.value for f in report.findings] == ["POTENTIAL_CONFLICT", "MATCH_FOUND", "MATCH_FOUND"]
    for finding in report.findings:
        for ev in finding.evidence:
            assert ev.quote == doc.pages[ev.page-1].text[ev.start:ev.end]
    assert offline_model._passages == []
    assert offline_model._embeddings is None
