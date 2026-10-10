from datetime import date
from pathlib import Path
import pytest
from evaluation.generate_fixtures import create_pdf
from polisdiff.engine import evaluate, load_catalogue, topic, extract_value
from polisdiff.extraction import extract_pdf
from polisdiff.retrieval import Retriever
from polisdiff.service import analyze_pdf
from polisdiff.text import normalize

RULES = {r.id: r for r in load_catalogue()[1]}


@pytest.mark.parametrize("days,status", [(3, "MATCH_FOUND"), (9, "POTENTIAL_CONFLICT")])
def test_russian_transfer_payment_independent(tmp_path, days, status):
    path = tmp_path / "independent.pdf"
    # Newly authored regression cases; exposed during this audit, not a holdout.
    create_pdf(path, [["Тест аудита ОСАГО. 19.03.2026.",
        f"Страховое возмещение перечисляется получателю в срок {days} рабочих дней после принятия решения страховщиком."]])
    doc, report = analyze_pdf(path.read_bytes(), date(2026, 10, 10), date(2026, 3, 19), Retriever("lexical"))
    finding = report.findings[1]
    assert finding.status.value == status
    assert finding.evidence[0].extracted_value == days
    ev = finding.evidence[0]
    assert ev.quote == doc.pages[ev.page-1].text[ev.start:ev.end]


@pytest.mark.parametrize("text", [
    "Страховое возмещение перечисляется в течение 4 рабочих дней после принятия заявления; решение страховщика оформляется отдельно.",
    "Страховое возмещение перечисляется в течение 4 рабочих дней после принятия решения суда.",
    "Страховое возмещение не перечисляется в течение 4 рабочих дней после принятия решения страховщика.",
    "Если подтверждены расходы, страховое возмещение перечисляется в течение 4 рабочих дней после принятия решения страховщика.",
])
def test_transfer_wrong_trigger_or_negation_abstains(text):
    value, unit, problem = extract_value(RULES["OSAGO_PAYMENT"], normalize(text))
    assert problem


def test_notice_of_transfer_is_not_payment():
    text = normalize("Страхователю сообщается решение о перечислении страхового возмещения в течение 4 рабочих дней после принятия решения страховщика.")
    assert not topic(RULES["OSAGO_PAYMENT"], text)


def test_request_mentions_are_not_notice_trigger():
    text = normalize("Страхователю сообщается решение о страховом возмещении в течение 12 дней после ДТП; письменное заявление хранится в деле.")
    assert extract_value(RULES["OSAGO_DECISION_NOTICE"], text)[2]


def test_prepare_empty_clears_embeddings():
    retriever = Retriever("lexical")
    retriever._embeddings = object()
    retriever.prepare([])
    assert retriever._embeddings is None


def test_runtime_retrievers_do_not_share_query_or_document_state(monkeypatch):
    from polisdiff import runtime
    base = Retriever('lexical')
    base.model = object()
    base._query_vectors = {('static',): object()}
    runtime._ai_base.cache_clear()
    monkeypatch.setattr(runtime, 'Retriever', lambda mode: base)
    try:
        a, b = runtime.web_retriever('hybrid'), runtime.web_retriever('semantic')
        a._query_vectors[('session-a',)] = object()
        a._passages.append(object())
        assert ('session-a',) not in b._query_vectors
        assert ('session-a',) not in base._query_vectors
        assert not b._passages and not base._passages
        assert a.model is b.model
    finally:
        runtime._ai_base.cache_clear()


def test_optional_bad_model_manifest_does_not_mislabel_loaded_model(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    import polisdiff.retrieval as module
    model_path = tmp_path/'model'
    model_path.mkdir()
    (model_path/'config.json').write_text('{}')
    (tmp_path/'evaluation').mkdir()
    (tmp_path/'evaluation/model_manifest.json').write_text('{}')
    fake_model = SimpleNamespace(max_seq_length=0)
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(set_num_threads=lambda _: None))
    monkeypatch.setitem(sys.modules, 'sentence_transformers', SimpleNamespace(SentenceTransformer=lambda *a,**k:fake_model))
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    r = module.Retriever('semantic', model_path=model_path)
    assert r.used == 'semantic' and r.model is fake_model and r.model_revision is None


def test_isolated_worker_timeouts_and_busy_cleanup(monkeypatch):
    import subprocess
    import polisdiff.extraction as extraction
    import polisdiff.service as service
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs['timeout'])
    monkeypatch.setattr(extraction.subprocess, 'run', timeout)
    r = Retriever('lexical')
    r._passages = [object()]
    r._embeddings = object()
    with pytest.raises(extraction.PDFError, match='25 seconds'):
        service.analyze_pdf(b'%PDF-1.7', date(2026,10,10), None, r)
    assert not r._passages and r._embeddings is None
    assert service._ANALYSIS_GATE.acquire(blocking=False)
    try:
        with pytest.raises(service.BusyError):
            service.analyze_pdf(b'%PDF-1.7', date(2026,10,10), None, r)
    finally:
        service._ANALYSIS_GATE.release()
    with pytest.raises(extraction.PDFError, match='timed out'):
        extraction.render_page(b'%PDF-1.7', 1)
    with pytest.raises(extraction.PDFError, match='Invalid page'):
        extraction.render_page(b'%PDF-1.7', True)


def test_contradictory_values_do_not_become_conflict_or_match(tmp_path):
    path = tmp_path/'competing.pdf'
    create_pdf(path, [["ОСАГО. Страховая сумма 80 миллионов сум.",
        "Страховая сумма 55 миллионов сум."]])
    doc = extract_pdf(path.read_bytes())
    finding = evaluate(RULES['OSAGO_SUM'], doc, doc.passages, date(2026,1,5), date(2026,10,10))
    assert finding.status.value == 'UNVERIFIABLE'
    assert finding.uncertainty == ['competing_or_ambiguous_terms']


def test_actual_progress_callbacks_follow_execution(tmp_path):
    path = tmp_path/'progress.pdf'
    create_pdf(path, [["Оригинальный текст ОСАГО, без числового условия."]])
    stages = []
    analyze_pdf(path.read_bytes(), date(2026,10,10), None, Retriever('lexical'), on_progress=stages.append)
    assert stages == ['extraction','retrieval','evaluation','report']


def test_retrieval_does_not_hide_competing_offer_value(tmp_path):
    from polisdiff.service import audit_document
    path = tmp_path/'ranked.pdf'
    create_pdf(path, [["Страховая сумма 80 миллионов сум."], ["Страховая сумма 55 миллионов сум."]])
    doc = extract_pdf(path.read_bytes())
    r = Retriever('lexical')
    r.search = lambda queries, k: [(doc.passages[0], 1)]
    report = audit_document(doc,date(2026,10,10),date(2026,1,5),r)
    assert report.findings[0].status.value == 'UNVERIFIABLE'
    assert {e.page for e in report.findings[0].evidence} == {1,2}
    assert report.candidate_selection == 'top_8_per_section_plus_offer_topic_guard'


@pytest.mark.parametrize('applicable,audit', [(None,date(2026,10,10)),
    (date(2023,1,1),date(2026,10,10)),(date(2027,1,1),date(2027,1,1)),
    (date(2026,1,5),date(2025,1,1))])
def test_unknown_unsupported_dates_have_no_selected_legal_target(tmp_path, applicable, audit):
    path = tmp_path/'date.pdf'
    create_pdf(path, [["Страховая сумма 80 миллионов сум."]])
    doc, report = analyze_pdf(path.read_bytes(),audit,applicable,Retriever('lexical'))
    assert all(f.status.value == 'UNVERIFIABLE' for f in report.findings)
    assert all(f.expected_value is None and not f.source_quote and f.effective_from is None for f in report.findings)


def test_actual_inson_boundary_when_provisioned():
    # Reproduction is optional on clean clones; synthetic boundary is mandatory below.
    path = Path(__file__).resolve().parents[1] / "local_data/sources/inson_russian.pdf"
    if path.exists():
        doc = extract_pdf(path.read_bytes())
        assert len(doc.pages) == 66
        assert all(p.section == "offer" for p in doc.pages[:8])
        assert all(p.section == "regulatory_appendix" for p in doc.pages[8:])


def test_split_heading_appendix_remains_excluded(tmp_path):
    path = tmp_path / "split.pdf"
    create_pdf(path, [["Оферта ОСАГО. См. правила по постановлению №141."],
        ["ПРИЛОЖ ЕНИЕ К ОФЕРТЕ", "ПРАВИЛА", "обязательного страхования",
         "Приложение №4 к постановлению от 24 июня 2008 г. №141",
         "Страховая сумма 80 миллионов сум."], ["Страховая сумма 80 миллионов сум."]])
    doc = extract_pdf(path.read_bytes())
    assert [p.section for p in doc.pages] == ["offer", "regulatory_appendix", "regulatory_appendix"]
    finding = evaluate(RULES["OSAGO_SUM"], doc, doc.passages, date(2026, 1, 5), date(2026, 10, 10))
    assert finding.status.value == "UNVERIFIABLE"
    assert finding.uncertainty == ["appendix_only"]
