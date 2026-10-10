"""Run inside a network-disabled container with read-only public/synthetic mounts."""
from datetime import date, datetime, timezone
from pathlib import Path
import hashlib
import json
import resource
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from polisdiff.retrieval import Retriever
from polisdiff.service import analyze_pdf
from polisdiff.extraction import render_page

def main():
    retriever = Retriever("hybrid")
    assert retriever.model is not None, retriever.warning
    cases = [(language,Path(f"/fixtures/evaluation/{language}_sum_conflict.pdf"),date(2026,1,5),True)
        for language in ["uz-Latn","uz-Cyrl","ru-Cyrl"]]
    cases += [(key,Path(f"/sources/{key}.pdf"),applicable,False) for key,applicable in
        [("gross_latin",date(2026,1,5)),("gross_cyrillic",date(2024,9,6)),("inson_russian",date(2026,1,15))]]
    rows = []
    for key,path,applicable,labelled in cases:
        started = time.perf_counter()
        doc,report = analyze_pdf(path.read_bytes(),date(2026,10,10),applicable,retriever)
        statuses = [f.status.value for f in report.findings]
        if labelled:
            assert statuses == ["POTENTIAL_CONFLICT","MATCH_FOUND","MATCH_FOUND"],(key,statuses)
        for finding in report.findings:
            for ev in finding.evidence:
                assert ev.quote == doc.pages[ev.page-1].text[ev.start:ev.end]
        rows.append({"id":key,"statuses":statuses,"page_count":len(doc.pages),"languages":doc.languages,
            "end_to_end_seconds":time.perf_counter()-started,"evidence_verified":True})
    assert render_page(cases[0][1].read_bytes(),2).startswith(b"\x89PNG")
    print(json.dumps({"checked_at":datetime.now(timezone.utc).isoformat(),"network":"none",
        "root_filesystem":"read_only","uid":__import__('os').getuid(),"success":True,
        "model_revision":retriever.model_revision,"model_initialization_seconds":retriever.initialization_seconds,
        "peak_main_process_rss_mib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        "source_code_sha256":{str(path.relative_to('/app')):hashlib.sha256(path.read_bytes()).hexdigest() for path in
            [Path('/app/app.py'),Path('/app/main.py'),Path('/app/rules/catalogue.v1.json'),
             Path('/app/Dockerfile'),Path('/app/requirements.runtime.lock.txt'),Path('/app/.streamlit/config.toml'),
             *sorted(Path('/app/polisdiff').glob('*.py'))]},
        "cases":rows,"raster_preview_verified":True},ensure_ascii=False))

if __name__ == "__main__":
    main()
