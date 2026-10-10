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
