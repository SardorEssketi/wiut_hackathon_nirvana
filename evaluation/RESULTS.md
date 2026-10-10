# Actual evaluation results

Measurement timestamp: 2026-10-10T10:20:31.978328+00:00. Platform: Windows-11-10.0.26200-SP0.

See [raw measurements](benchmark_results.json), [dataset manifest](dataset_manifest.json),
[fresh wording](blind_fixtures.json), [source hashes](source_manifest.json), and [model hashes](model_manifest.json).

## Results by dataset

| Mode / dataset | Docs | Labelled statuses | Status accuracy | Conflict precision | Conflict recall | Recall@1 / @3 / @8 | Median / max analysis s | Abstention |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: |
| lexical / regression_evaluation | 27 | 81 | 100.0% | 100.0% | 100.0% | 100.0% / 100.0% / 100.0% | 0.466 / 0.662 | 25.9% |
| lexical / fresh_evaluation | 3 | 9 | 88.9% | 100.0% | 80.0% | 100.0% / 100.0% / 100.0% | 0.531 / 0.662 | 0.0% |
| lexical / real | 3 | 0 | not labelled | not labelled | not labelled | 80.0% / 100.0% / 100.0% | 0.725 / 1.290 | 88.9% |
| semantic / regression_evaluation | 27 | 81 | 93.8% | 100.0% | 100.0% | 98.6% / 100.0% / 100.0% | 0.877 / 1.341 | 25.9% |
| semantic / fresh_evaluation | 3 | 9 | 88.9% | 100.0% | 80.0% | 66.7% / 100.0% / 100.0% | 0.599 / 0.739 | 0.0% |
| semantic / real | 3 | 0 | not labelled | not labelled | not labelled | 60.0% / 60.0% / 100.0% | 9.326 / 28.901 | 100.0% |
| hybrid / regression_evaluation | 27 | 81 | 100.0% | 100.0% | 100.0% | 98.6% / 100.0% / 100.0% | 0.670 / 0.796 | 25.9% |
| hybrid / fresh_evaluation | 3 | 9 | 88.9% | 100.0% | 80.0% | 100.0% / 100.0% / 100.0% | 0.489 / 0.516 | 0.0% |
| hybrid / real | 3 | 0 | not labelled | not labelled | not labelled | 60.0% / 100.0% / 100.0% | 6.164 / 25.717 | 100.0% |

## Languages evaluated separately — fresh wording

| Mode | Language | Labelled statuses | Correct statuses | Recall@3 | Evidence expected-page accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| lexical | ru-Cyrl | 3 | 66.7% | 100.0% | 100.0% |
| lexical | uz-Cyrl | 3 | 100.0% | 100.0% | 100.0% |
| lexical | uz-Latn | 3 | 100.0% | 100.0% | 100.0% |
| semantic | ru-Cyrl | 3 | 66.7% | 100.0% | 100.0% |
| semantic | uz-Cyrl | 3 | 100.0% | 100.0% | 100.0% |
| semantic | uz-Latn | 3 | 100.0% | 100.0% | 100.0% |
| hybrid | ru-Cyrl | 3 | 66.7% | 100.0% | 100.0% |
| hybrid | uz-Cyrl | 3 | 100.0% | 100.0% | 100.0% |
| hybrid | uz-Latn | 3 | 100.0% | 100.0% | 100.0% |

## Extraction, timing and memory

Peak benchmark process-tree resident memory: **1373.3 MiB**. This excludes the separately running Streamlit/browser processes.

| Mode | Actual mode | Model initialization seconds | Returned evidence exact-text tracing |
| --- | --- | ---: | ---: |
| lexical | lexical | 0.000 | 100.0% / 100.0% / 100.0% |
| semantic | semantic | 23.613 | 100.0% / 100.0% / 100.0% |
| hybrid | hybrid | 23.613 | 100.0% / 100.0% / 100.0% |

Pipeline exceptions: 0 / 99 measured document/mode executions. Abstentions are reported separately above.

Whitespace-normalized synthetic character similarity: min 1.000000, mean 1.000000 over 30 PDFs.
No transcription ground truth exists for real documents, so no real extraction/OCR CER is claimed.

Latency includes isolated extraction, retrieval and deterministic evaluation, excludes model initialization and measurement-only extra retrieval probes. Single run per input; cached legal-query embeddings. Other local verification/build tasks may contend for CPU. No throughput/SLA claim.

## Failures and interpretation

The Russian fresh payment phrase `перечисляется` was retrieved at the correct page but was not recognized by the deterministic event extractor; one of five fresh conflicts was missed in all modes. The rule engine was not changed based on these fresh outcomes.

The 27-document evaluation wording was exposed during debugging and is therefore reported as regression evaluation. Fresh evaluation has only three separately authored documents / nine rule labels. Neither is expert legal ground truth. The small data does not establish an AI accuracy improvement over the lexical baseline.

Recall@K is averaged over manually labelled relevant-page queries, separately within the offer/appendix region that contains the label, matching production's per-region top-K. Correct quote offsets are a tracing check; they are not proof of legal relevance. Real-document rule precision/recall remains unlabelled.

Public PDFs demonstrate extraction imperfections and reference/appendix abstention. These are reported rather than replaced with synthetic answers. Language accuracy itself is not measured against an independent annotated corpus. OCR was absent and remains disabled.

The original benchmark mistakenly concatenated regional rankings for Recall@K. This report uses corrected per-region accounting; the engine/labels were unchanged. No initial inaccurate retrieval metric is claimed as a final result.
