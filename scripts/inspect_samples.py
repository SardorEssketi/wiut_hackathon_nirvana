from datetime import date
from pathlib import Path
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from polisdiff.extraction import extract_pdf
from polisdiff.engine import load_catalogue, topic, extract_value
from polisdiff.retrieval import Retriever
from polisdiff.service import audit_document

ROOT = Path(__file__).resolve().parents[1]

def main():
    _, rules, _ = load_catalogue()
    rows = []
    for key, applicable in [("gross_latin", date(2026,1,5)), ("gross_cyrillic", date(2024,9,6)), ("inson_russian", date(2026,1,15))]:
        doc = extract_pdf((ROOT / "local_data" / "sources" / (key+".pdf")).read_bytes())
        report = audit_document(doc, date(2026,10,10), applicable, Retriever("lexical"))
        row = {"id": key, "sha256": doc.sha256, "pages": len(doc.pages), "passages": len(doc.passages),
            "languages": doc.languages, "characters": sum(p.chars for p in doc.pages), "warnings": doc.warnings,
            "appendix_pages": [p.number for p in doc.pages if p.section != "offer"],
            "results": {f.rule_id: {"status": f.status.value, "reason": f.reason, "pages": [e.page for e in f.evidence]} for f in report.findings}}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
        for rule in rules:
            for p in doc.passages:
                if topic(rule, p.normalized):
                    print(rule.id, "page", p.page, p.section, extract_value(rule, p.normalized), repr(p.text[:300]))
        (ROOT / "local_data" / (key+"_extracted.json")).write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    (ROOT / "evaluation" / "real_extraction.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
