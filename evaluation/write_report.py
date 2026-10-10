"""Produce prose tables directly from measured artifacts; no hand-entered metrics."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def fmt(value, percent=False):
    if value is None:
        return "not labelled"
    return f"{value*100:.1f}%" if percent else f"{value:.3f}"


def main():
    result = json.loads((ROOT/"evaluation/benchmark_results.json").read_text(encoding="utf-8"))
    lines = ["# Actual evaluation results", "", f"Measurement timestamp: {result['created_at']}. Platform: {result['platform']}.", "",
        "See [raw measurements](benchmark_results.json), [dataset manifest](dataset_manifest.json),",
        "[fresh wording](blind_fixtures.json), [source hashes](source_manifest.json), and [model hashes](model_manifest.json).", "",
        "## Results by dataset", "",
        "| Mode / dataset | Docs | Labelled statuses | Status accuracy | Conflict precision | Conflict recall | Recall@1 / @3 / @8 | Median / max analysis s | Abstention |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |"]
    for mode,row in result["modes"].items():
        for split in ["regression_evaluation","fresh_evaluation","real"]:
            s = row["summary_by_split"][split]
            lines.append(f"| {mode} / {split} | {s['documents']} | {s['labelled_rule_results']} | {fmt(s['rule_status_accuracy'],True)} | {fmt(s['conflict_precision'],True)} | {fmt(s['conflict_recall'],True)} | " +
                " / ".join(fmt(s[f"retrieval_recall_at_{k}"],True) for k in [1,3,8])+f" | {fmt(s['latency_median_seconds'])} / {fmt(s['latency_max_seconds'])} | {fmt(s['abstention_rate'],True)} |")
    lines.extend(["", "## Languages evaluated separately — fresh wording", "",
        "| Mode | Language | Labelled statuses | Correct statuses | Recall@3 | Evidence expected-page accuracy |", "| --- | --- | ---: | ---: | ---: | ---: |"])
    for mode,row in result["modes"].items():
        for lang, splits in sorted(row["summary_by_language_and_split"].items()):
            s = splits["fresh_evaluation"]
            lines.append(f"| {mode} | {lang} | {s['labelled_rule_results']} | {fmt(s['rule_status_accuracy'],True)} | {fmt(s['retrieval_recall_at_3'],True)} | {fmt(s['evidence_expected_page_accuracy'],True)} |")
    lines.extend(["", "## Extraction, timing and memory", "",
        f"Peak benchmark process-tree resident memory: **{result['peak_process_tree_rss_mib']:.1f} MiB**. This excludes the separately running Streamlit/browser processes.", "",
        "| Mode | Actual mode | Model initialization seconds | Returned evidence exact-text tracing |", "| --- | --- | ---: | ---: |"])
    for mode,row in result["modes"].items():
        lines.append(f"| {mode} | {row['actual_mode']} | {row['model_initialization_seconds']:.3f} | " +
            " / ".join(fmt(row["summary_by_split"][s]["evidence_text_traceability"],True) for s in ["regression_evaluation","fresh_evaluation","real"])+" |")
    extraction = [r["extraction_character_similarity"] for r in result["modes"]["lexical"]["cases"] if r.get("extraction_character_similarity") is not None]
    executions = [r for mode in result["modes"].values() for r in mode["cases"]]
    failed = sum(bool(r.get("error")) for r in executions)
    lines.extend(["",f"Pipeline exceptions: {failed} / {len(executions)} measured document/mode executions. Abstentions are reported separately above.",
        "",f"Whitespace-normalized synthetic character similarity: min {min(extraction):.6f}, mean {sum(extraction)/len(extraction):.6f} over {len(extraction)} PDFs.",
        "No transcription ground truth exists for real documents, so no real extraction/OCR CER is claimed.", "",
        "Latency includes isolated extraction, retrieval and deterministic evaluation, excludes model initialization and measurement-only extra retrieval probes. Single run per input; cached legal-query embeddings. Other local verification/build tasks may contend for CPU. No throughput/SLA claim.", "",
        "## Failures and interpretation", "",
        "The Russian fresh payment phrase `перечисляется` was retrieved at the correct page but was not recognized by the deterministic event extractor; one of five fresh conflicts was missed in all modes. The rule engine was not changed based on these fresh outcomes.", "",
        "The 27-document evaluation wording was exposed during debugging and is therefore reported as regression evaluation. Fresh evaluation has only three separately authored documents / nine rule labels. Neither is expert legal ground truth. The small data does not establish an AI accuracy improvement over the lexical baseline.", "",
        "Recall@K is averaged over manually labelled relevant-page queries, separately within the offer/appendix region that contains the label, matching production's per-region top-K. Correct quote offsets are a tracing check; they are not proof of legal relevance. Real-document rule precision/recall remains unlabelled.", "",
        "Public PDFs demonstrate extraction imperfections and reference/appendix abstention. These are reported rather than replaced with synthetic answers. Language accuracy itself is not measured against an independent annotated corpus. OCR was absent and remains disabled.", "",
        "The original benchmark mistakenly concatenated regional rankings for Recall@K. This report uses corrected per-region accounting; the engine/labels were unchanged. No initial inaccurate retrieval metric is claimed as a final result.", ""])
    (ROOT/"evaluation/RESULTS.md").write_text("\n".join(lines),encoding="utf-8")
    print("Generated evaluation/RESULTS.md from actual measurements")

if __name__ == "__main__":
    main()
