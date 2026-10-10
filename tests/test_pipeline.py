from datetime import date
from pathlib import Path
import json
import pytest
import pymupdf
from polisdiff.extraction import extract_pdf, PDFError, MAX_BYTES, render_page
from polisdiff.text import normalize, detect_languages, parse_number
from polisdiff.engine import load_catalogue
from polisdiff.retrieval import Retriever
from polisdiff.service import analyze_pdf, audit_document
from polisdiff.export import html_report, add_review
from evaluation.generate_fixtures import create_pdf

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "evaluation/dataset_manifest.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("row", MANIFEST, ids=lambda r: r["split"]+"/"+r["id"])
def test_original_labelled_fixtures(row):
    document, report = analyze_pdf((ROOT / row["path"]).read_bytes(), date(2026,10,10),
        date.fromisoformat(row["applicable_date"]) if row["applicable_date"] else None, Retriever("lexical"))
    assert {f.rule_id: f.status.value for f in report.findings} == row["expected"]
    assert row["language"] in document.languages
    for finding in report.findings:
        assert finding.reviewer_status == "PENDING_LEGAL_REVIEW"
        assert finding.manual_review_required
        for ev in finding.evidence:
            assert document.pages[ev.page-1].text[ev.start:ev.end] == ev.quote
            assert ev.bbox[0] <= ev.bbox[2] and ev.bbox[1] <= ev.bbox[3]


@pytest.mark.parametrize("variant", ["o‘", "oʻ", "o'", "o’", "oʼ"])
def test_apostrophe_search_and_original_preservation(variant):
    assert normalize(variant) == "o'"


@pytest.mark.parametrize("text,expected", [("80 000 000", 80000000), ("80.000.000",80000000),
    ("80,000,000",80000000), ("80\u202f000\u202f000",80000000), ("80,5",80.5), ("80.5",80.5), ("1.234,50",1234.5), ("1,234.50",1234.5)])
def test_numeric_conventions(text, expected):
    assert parse_number(text) == expected


def test_mixed_language_detection():
    labels = detect_languages("Суғурта товони. Страховое возмещение. Sugʻurta summasi.")
    assert set(labels) == {"uz-Latn", "uz-Cyrl", "ru-Cyrl"}
    assert detect_languages("АБВ") == ["Cyrillic-undetermined"]


@pytest.mark.parametrize("data", [b"", b"not a PDF", b"%PDF-1.7\nmalformed", b"%PDF-"+b"x"*MAX_BYTES], ids=["empty", "bad_header", "malformed", "oversize"])
def test_reject_invalid_pdf(data):
    with pytest.raises(PDFError):
        extract_pdf(data)


def test_encrypted_pdf_rejected():
    doc = pymupdf.open()
    doc.new_page()
    data = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="user")
    with pytest.raises(PDFError):
        extract_pdf(data)


def test_too_many_pages_rejected():
    doc = pymupdf.open()
    for _ in range(81):
        doc.new_page()
    with pytest.raises(PDFError):
        extract_pdf(doc.tobytes())


def test_scan_abstains():
    doc = pymupdf.open()
    page = doc.new_page()
    page.draw_rect(pymupdf.Rect(20,20,300,300), color=(.2,.5,.8), fill=(.2,.5,.8))
    extracted = extract_pdf(doc.tobytes())
    report = audit_document(extracted, date(2026,10,10), date(2026,1,5), Retriever("lexical"))
    assert all(f.status.value == "UNVERIFIABLE" for f in report.findings)
    assert extracted.warnings


def test_unsupported_date_and_audit_order():
    doc = extract_pdf((ROOT / "tests/fixtures/development/ru-Cyrl_match.pdf").read_bytes())
    for applicable, audit in [(date(2023,1,1),date(2026,10,10)), (date(2027,1,1),date(2027,1,1)), (date(2026,1,5),date(2025,1,1))]:
        report = audit_document(doc, audit, applicable, Retriever("lexical"))
        assert all(f.status.value == "UNVERIFIABLE" for f in report.findings)


def test_governing_appendix_separate(tmp_path):
    path = tmp_path / "appendix.pdf"
    create_pdf(path, [["Публичная оферта. Договор ссылается на постановление №141 и правила страхования."],
        ["Приложение №1 к постановлению Кабинета Министров от 24.06.2008 №141",
         "ПРАВИЛА обязательного страхования", "Страховая сумма 80 миллионов сум.",
         "Выплата страхового возмещения осуществляется в течение 5 рабочих дней со дня принятия решения страховщика."]])
    doc = extract_pdf(path.read_bytes())
    assert doc.pages[0].section == "offer"
    assert doc.pages[1].section == "regulatory_appendix"
    report = audit_document(doc,date(2026,10,10),date(2026,1,5),Retriever("lexical"))
    assert report.findings[0].status.value == "UNVERIFIABLE"
    assert all(e.section == "regulatory_appendix" for e in report.findings[0].evidence)


def test_safely_escaped_export_and_audit_record():
    doc = extract_pdf((ROOT / "tests/fixtures/development/ru-Cyrl_match.pdf").read_bytes())
    report = audit_document(doc,date(2026,10,10),date(2026,1,5),Retriever("lexical"))
    add_review(report,"OSAGO_SUM","dismiss","<script>alert(1)</script>")
    exported = html_report(report)
    assert "<script>" not in exported
    assert "&lt;script&gt;" in exported
    assert report.reviews[0].timestamp.tzinfo is not None
    with pytest.raises(ValueError):
        add_review(report,"not_a_rule","confirm","reason")
    assert len(report.reviews) == 1


def test_raster_preview():
    data = (ROOT / "tests/fixtures/development/ru-Cyrl_match.pdf").read_bytes()
    assert render_page(data, 2).startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize("page", [0, -1, 81, "2", None])
def test_invalid_preview_page(page):
    data = (ROOT / "tests/fixtures/development/ru-Cyrl_match.pdf").read_bytes()
    with pytest.raises(PDFError):
        render_page(data, page)


def test_web_modes_share_model_without_upload_state(monkeypatch):
    from polisdiff import runtime
    calls = []
    def fake(mode):
        calls.append(mode)
        instance = Retriever("lexical")
        instance.model = object()
        return instance
    runtime._ai_base.cache_clear()
    monkeypatch.setattr(runtime, "Retriever", fake)
    try:
        hybrid = runtime.web_retriever("hybrid")
        semantic = runtime.web_retriever("semantic")
        assert calls == ["hybrid"]
        assert hybrid.model is semantic.model
        assert hybrid.used == "hybrid" and semantic.used == "semantic"
        assert hybrid._passages is not semantic._passages
    finally:
        runtime._ai_base.cache_clear()


def test_model_failure_is_explicit(tmp_path):
    retriever = Retriever("hybrid", model_path=tmp_path)
    assert retriever.used == "lexical"
    assert "unavailable" in retriever.warning


def test_rules_have_provenance_and_pending_review():
    data, rules, digest = load_catalogue()
    assert len(rules) == 3 and len(digest) == 64
    assert data["verified_access_date"] == "2026-10-10"
    for rule in rules:
        assert rule.reviewer_status == "PENDING_LEGAL_REVIEW"
        assert rule.official_source.startswith("https://lex.uz/")
        assert rule.reference and rule.extraction_requirements and rule.uncertainty_conditions


def test_unseen_original_fixture(tmp_path):
    # This wording is separate from development and benchmark templates.
    path = tmp_path / "unseen.pdf"
    create_pdf(path, [["Оригинальный тест ОСАГО. 20.02.2026.", "Страховая сумма установлена как 61 234 567 сум.",
        "Выплата страхового возмещения осуществляется в срок 4 рабочих дня со дня принятия решения страховщика.",
        "Решение о страховом возмещении сообщено страхователю через 14 дней после письменного обращения."]])
    doc, report = analyze_pdf(path.read_bytes(),date(2026,10,10),date(2026,2,20),Retriever("lexical"))
    assert [f.status.value for f in report.findings] == ["POTENTIAL_CONFLICT", "MATCH_FOUND", "MATCH_FOUND"]
    assert report.findings[0].evidence[0].extracted_value == 61234567
    for finding in report.findings:
        for ev in finding.evidence:
            assert ev.quote == doc.pages[ev.page-1].text[ev.start:ev.end]
