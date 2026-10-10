"""Recheck public files without overwriting historical results or redistributing quotations."""
from datetime import date, datetime, timezone
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from polisdiff.engine import load_catalogue, topic, extract_value
from polisdiff.extraction import extract_pdf, render_page
from polisdiff.service import audit_document
from polisdiff.retrieval import Retriever

ROOT = Path(__file__).resolve().parents[1]


def main():
    dest = ROOT / 'local_data/audit_public'
    dest.mkdir(parents=True, exist_ok=True)
    annotations = json.loads((ROOT/'evaluation/real_annotations.json').read_text(encoding='utf-8'))
    rules = load_catalogue()[1]
    retriever = Retriever('hybrid')
    rows = []
    for case in annotations['cases']:
        data = (ROOT/f"local_data/sources/{case['id']}.pdf").read_bytes()
        doc = extract_pdf(data)
        report = audit_document(doc, date(2026,10,10), date.fromisoformat(case['applicable_date']), retriever)
        (dest/f"{case['id']}.json").write_text(report.model_dump_json(indent=2), encoding='utf-8')
        (dest/f"{case['id']}.extracted.json").write_text(doc.model_dump_json(indent=2), encoding='utf-8')
        findings = []
        for rule, finding in zip(rules, report.findings):
            topical = [p for p in doc.passages if topic(rule, p.normalized)]
            probes = [{'page':p.page,'section':p.section,'value':extract_value(rule,p.normalized)[0],
                       'unit':extract_value(rule,p.normalized)[1], 'problem':extract_value(rule,p.normalized)[2]}
                      for p in topical]
            findings.append({'rule_id':rule.id,'status':finding.status.value,'reason':finding.reason,
                'uncertainty':finding.uncertainty,'evidence_pages':[e.page for e in finding.evidence],
                'topical_passage_probes':probes})
        pages_to_view = sorted({p for pages in case['relevant_pages'].values() for p in pages})
        if case['id'] == 'inson_russian': pages_to_view += [8,9]
        for page in pages_to_view:
            (dest/f"{case['id']}.page{page}.png").write_bytes(render_page(data,page))
        rows.append({'id':case['id'],'sha256':doc.sha256,'applicable_date':case['applicable_date'],
            'pages':len(doc.pages),'appendix_pages':[p.number for p in doc.pages if p.section!='offer'],
            'warnings':doc.warnings,'retrieval_requested':report.retrieval_requested,'retrieval_used':report.retrieval_used,
            'findings':findings})
        print(case['id'], [f.status.value for f in report.findings], flush=True)
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'legal_status_labels':False,'cases':rows}
    (ROOT/'evaluation/audit_public_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
