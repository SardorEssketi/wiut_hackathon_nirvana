"""Actual metrics; separate regression, fresh wording, and public-document measurements."""
from collections import defaultdict
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
import argparse
import hashlib
import json
import platform
import statistics
import sys
import threading
import time
import psutil
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.generate_fixtures import create_pdf, RULE_IDS
from polisdiff.extraction import extract_pdf
from polisdiff.engine import load_catalogue
from polisdiff.models import Document
from polisdiff.retrieval import Retriever
from polisdiff.service import audit_document

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "evaluation"


class MemorySampler:
    def __init__(self):
        self.peak = 0
        self.stop = threading.Event()
        self.process = psutil.Process()
        self.thread = threading.Thread(target=self.sample, daemon=True)
    def sample(self):
        while not self.stop.is_set():
            try:
                rss = self.process.memory_info().rss + sum(p.memory_info().rss for p in self.process.children(recursive=True) if p.is_running())
                self.peak = max(self.peak, rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            self.stop.wait(.05)
    def __enter__(self):
        self.thread.start()
        return self
    def __exit__(self,*args):
        self.stop.set()
        self.thread.join()


def ratio(a,b):
    return a/b if b else None


def summarize(rows):
    labels = [f for row in rows for f in row["findings"] if f["expected"] is not None]
    tp = sum(f["actual"] == f["expected"] == "POTENTIAL_CONFLICT" for f in labels)
    fp = sum(f["actual"] == "POTENTIAL_CONFLICT" and f["expected"] != "POTENTIAL_CONFLICT" for f in labels)
    fn = sum(f["expected"] == "POTENTIAL_CONFLICT" and f["actual"] != "POTENTIAL_CONFLICT" for f in labels)
    all_findings = [f for row in rows for f in row["findings"]]
    evidence = [ev for row in rows for f in row["findings"] for ev in f["evidence_checks"]]
    page_checks = [ev["expected_page_correct"] for ev in evidence if ev["expected_page_correct"] is not None]
    retrieval = [test for row in rows for test in row["retrieval_checks"]]
    latencies = [row["latency_seconds"] for row in rows if not row.get("error")]
    return {"documents": len(rows), "labelled_rule_results":len(labels),
        "rule_status_accuracy": ratio(sum(f["actual"] == f["expected"] for f in labels),len(labels)),
        "conflict_precision":ratio(tp,tp+fp), "conflict_recall":ratio(tp,tp+fn), "conflict_counts":{"tp":tp,"fp":fp,"fn":fn},
        "evidence_text_traceability":ratio(sum(e["exact_text"] for e in evidence),len(evidence)),
        "evidence_checks":len(evidence), "evidence_expected_page_accuracy":ratio(sum(page_checks),len(page_checks)),
        "expected_page_checks":len(page_checks),
        "retrieval_recall_at_1":ratio(sum(t["recall_at_1"] for t in retrieval),len(retrieval)),
        "retrieval_recall_at_3":ratio(sum(t["recall_at_3"] for t in retrieval),len(retrieval)),
        "retrieval_recall_at_8":ratio(sum(t["recall_at_8"] for t in retrieval),len(retrieval)),
        "retrieval_labelled_queries":len(retrieval),
        "abstention_rate":ratio(sum(f["actual"] == "UNVERIFIABLE" for f in all_findings),len(all_findings)),
        "failure_rate":ratio(sum(bool(r.get("error")) for r in rows),len(rows)),
        "latency_median_seconds":statistics.median(latencies) if latencies else None,
        "latency_max_seconds":max(latencies) if latencies else None}


def evaluate_case(case, retriever, rules):
    start = time.perf_counter()
    try:
        doc = extract_pdf((ROOT / case["path"]).read_bytes())
        extraction_time = time.perf_counter() - start
        extraction_score = None
        if case.get("ground_truth_pages"):
            expected = " ".join(" ".join(page) for page in case["ground_truth_pages"])
            actual = " ".join(p.text.rsplit("Synthetic fixture",1)[0] for p in doc.pages)
            extraction_score = SequenceMatcher(None," ".join(expected.split())," ".join(actual.split()),autojunk=False).ratio()
        report = audit_document(doc,date(2026,10,10), date.fromisoformat(case["applicable_date"]) if case["applicable_date"] else None,retriever)
        duration = time.perf_counter()-start
        checks = []
        # Search separately within offer and appendix as in production.
        candidate_pages = defaultdict(dict)
        for section in ["offer","regulatory_appendix","uncertain"]:
            subset = [p for p in doc.passages if p.section == section]
            retriever.prepare(subset)
            for rule in rules:
                candidate_pages[rule.id][section] = [p.page for p,_ in retriever.search(rule.queries,k=8)]
        for rule in rules:
            relevant = case["relevant_pages"].get(rule.id,[])
            if relevant:
                rankings = candidate_pages[rule.id]
                checks.append({"rule":rule.id, "relevant_pages":relevant,
                    **{f"recall_at_{k}":sum(page in rankings[doc.pages[page-1].section][:k] for page in set(relevant))/len(set(relevant)) for k in [1,3,8]}})
        finding_rows = []
        for finding in report.findings:
            expected = case.get("expected",{}).get(finding.rule_id)
            evidence_checks = [{"page":ev.page,"section":ev.section,
                "exact_text":doc.pages[ev.page-1].text[ev.start:ev.end] == ev.quote,
                "expected_page_correct":ev.page in case["relevant_pages"].get(finding.rule_id,[]) if
                    expected in {"MATCH_FOUND","POTENTIAL_CONFLICT"} else None} for ev in finding.evidence]
            finding_rows.append({"rule":finding.rule_id,"actual":finding.status.value,"expected":expected,
                "reason":finding.reason,"evidence_checks":evidence_checks})
        if case["split"] != "real":
            export_dir = OUTPUT_ROOT / "reports" / retriever.requested / case["split"]
            export_dir.mkdir(parents=True,exist_ok=True)
            (export_dir/(case["id"]+".json")).write_text(report.model_dump_json(indent=2),encoding="utf-8")
        return {"id":case["id"],"split":case["split"],"language":case["language"],"sha256":doc.sha256,
            "retrieval_requested":retriever.requested,"retrieval_used":retriever.used,"error":None,
            "latency_seconds":duration,"extraction_seconds":extraction_time,
            "extraction_character_similarity":extraction_score,"pages":len(doc.pages),
            "warnings":doc.warnings,"findings":finding_rows,"retrieval_checks":checks}
    except Exception as exc:
        return {"id":case["id"],"split":case["split"],"language":case["language"],"error":type(exc).__name__,
            "latency_seconds":time.perf_counter()-start,"findings":[],"retrieval_checks":[]}
    finally:
        retriever._passages = []
        retriever._embeddings = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modes", nargs="+",default=["lexical","semantic","hybrid"])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "evaluation",
                        help="Separate measurement directory; preserves historical artifacts.")
    parser.add_argument("--label", default="historical")
    args = parser.parse_args()
    global OUTPUT_ROOT
    OUTPUT_ROOT = args.output_dir.resolve()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    catalogue,rules,digest = load_catalogue()
    synthetic = json.loads((ROOT / "evaluation/dataset_manifest.json").read_text(encoding="utf-8"))
    cases = [dict(row, split="regression_evaluation") for row in synthetic if row["split"] == "evaluation"]
    blind = json.loads((ROOT / "evaluation/blind_fixtures.json").read_text(encoding="utf-8"))
    for row in blind["cases"]:
        pages = [["Original fresh synthetic OSAGO test. 05.02.2026.","Customer support hours 10:00–17:00."]] + [[term] for term in row["terms"]]
        path = f"tests/fixtures/blind/{row['id']}.pdf"
        # Existing fixtures are immutable inputs; create only if absent.
        if not (ROOT/path).exists():
            create_pdf(ROOT/path,pages)
        cases.append({"id":row["id"],"split":"fresh_evaluation","language":row["language"],"path":path,
            "applicable_date":"2026-02-05","expected":dict(zip(RULE_IDS,row["expected"])),
            "relevant_pages":dict(zip(RULE_IDS,[[2],[3],[4]])),"ground_truth_pages":pages})
    real = json.loads((ROOT / "evaluation/real_annotations.json").read_text(encoding="utf-8"))
    for row in real["cases"]:
        cases.append(dict(row, split="real",path=f"local_data/sources/{row['id']}.pdf"))
    result = {"created_at":datetime.now(timezone.utc).isoformat(),"python":sys.version,"platform":platform.platform(),
        "measurement_label": args.label,
        "cpu_logical":psutil.cpu_count(),"rules_catalogue_sha256":digest,
        "dataset_files_sha256":{name:hashlib.sha256((ROOT/"evaluation"/name).read_bytes()).hexdigest()
            for name in ["dataset_manifest.json","blind_fixtures.json","real_annotations.json"]},
        "limitations":["Small AI-authored engineering-labelled dataset; not expert legal validation.",
            "Regression evaluation wording was exposed during debugging; report separately from fresh evaluation.",
            "Real PDFs have page annotations only; no legal status labels or transcription ground truth.",
            "Character similarity is whitespace-normalized synthetic-text similarity; not OCR CER.",
            "Warm in-process query cache affects latency; model init reported separately. Single run per case."],
        "modes":{}}
    with MemorySampler() as memory:
        model = None
        for mode in args.modes:
            if mode == "lexical":
                retriever = Retriever("lexical")
            else:
                if model is None:
                    model = Retriever("hybrid")
                retriever = model
                retriever.requested = mode
                retriever.used = mode if retriever.model is not None else "lexical"
            rows = []
            for case in cases:
                row = evaluate_case(case,retriever,rules)
                rows.append(row)
                print(mode,case["split"],case["id"],"ERROR" if row["error"] else f"{row['latency_seconds']:.3f}s",flush=True)
            groups = {split:summarize([r for r in rows if r["split"]==split]) for split in {r["split"] for r in rows}}
            languages = {lang:{split:summarize([r for r in rows if r["language"]==lang and r["split"]==split])
                for split in groups} for lang in {r["language"] for r in rows}}
            result["modes"][mode] = {"actual_mode":retriever.used,"model_initialization_seconds":retriever.initialization_seconds,
                "warning":retriever.warning,"model_revision":retriever.model_revision,"summary_by_split":groups,
                "summary_by_language_and_split":languages,"cases":rows}
    result["peak_process_tree_rss_mib"] = memory.peak/1024**2
    (OUTPUT_ROOT / "benchmark_results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Measured peak process tree RSS:",round(result["peak_process_tree_rss_mib"],1),"MiB")

if __name__ == "__main__":
    main()
