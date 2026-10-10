# Redesign audit measurements — native localhost

Run date: 10 October 2026. Original measurements are preserved in
[RESULTS.md](RESULTS.md) and `benchmark_results.json`. These results refer to the
updated local application; they do not validate the previous Docker image or a
public deployment. Full issue details: [AUDIT_REPORT.md](../docs/AUDIT_REPORT.md).

## Baseline and automated tests

- Fresh pre-change suite: **67 passed, 0 failed, 0 errors, 0 skipped**, 27.11 s.
  [Baseline counts](audit_baseline_tests.json).
- Initial new defect probes: **7 failed, 4 passed** before fixes.
- Completed suite: **175 passed, 0 failed, 0 errors, 0 skipped**, 31.24 s.
  [Counts](audit_tests.json), [JUnit](audit_tests.xml).
- Existing tests retain their original expectations, including actual offline E5
  embeddings with sockets blocked. No failing assertion was removed or weakened.
- New tests cover all 64 combinations of three findings across four statuses, readable comparison
  values, no evidence, missing/unsupported dates, Unicode, long quotations,
  HTML escaping, unsafe URLs, JSON readability/round-trips, reviewer validation,
  fingerprint invalidation, evidence selection, scoped competing values,
  event/negation/condition distinctions, stale embeddings, model provenance and
  extraction/render timeouts. Browser tests exercise actual Streamlit widget state.

## Baseline reproduction and post-fix regression

[Baseline rerun](audit_baseline_benchmark.json) independently reproduced the
historical outcomes. [Final measurements](audit_benchmark_results.json) record all
99 document/mode executions, timings, source hashes, model revision, memory and
exact evidence-offset checks. The catalogue and fixture bytes were not changed.

| Data / mode | Labelled statuses | Baseline accuracy | Post-fix accuracy | Baseline conflict recall | Post-fix conflict recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Exposed original regression / lexical | 81 | 100% | 100% | 100% | 100% |
| Exposed original regression / semantic | 81 | 93.8% | 100% | 100% | 100% |
| Exposed original regression / hybrid | 81 | 100% | 100% | 100% | 100% |
| Former fresh, now exposed regression / lexical | 9 | 88.9% | 100% | 80% | 100% |
| Former fresh, now exposed regression / semantic | 9 | 88.9% | 100% | 80% | 100% |
| Former fresh, now exposed regression / hybrid | 9 | 88.9% | 100% | 80% | 100% |

The former-fresh Russian payment miss is fixed. The conservative offer-topic scan
also prevents a ranker from hiding lower-ranked/competing clauses and applies to
all modes. These small AI-assisted engineering-labelled sets influenced debugging;
**100% here is regression coverage, not independent AI accuracy or legal accuracy**.
No demonstrated AI accuracy improvement over lexical search is established.

All modes retain 100% returned-evidence exact-text traceability. This verifies
quoted text/page-relative offsets; it does not prove legal relevance or correct
interpretation. Public samples have no expert legal-status labels, so no public
accuracy/precision/recall is reported. Raw latency/memory values are single-machine
measurements, affected by concurrent browser/test work; they are not throughput or
an SLA. Model initialization is reported separately. Peak process-tree memory is
about 1.4 GiB; other concurrent tools/browser/server processes are excluded.

## Original public PDFs

[Current cause/page probes](audit_public_results.json) preserve source-byte hashes
and classify each finding. Full reports, extracted text and page images remain in
ignored `local_data/audit_public/` and are not redistributed in Git.

| Sample / selected applicability scenario | Total | Payment | Notification |
| --- | --- | --- | --- |
| GROSS Latin / 2026-01-05 | UNVERIFIABLE | UNVERIFIABLE | UNVERIFIABLE |
| GROSS Cyrillic / 2024-09-06 | POTENTIAL_CONFLICT | UNVERIFIABLE | UNVERIFIABLE |
| INSON Russian / 2026-01-15 | UNVERIFIABLE | UNVERIFIABLE | UNVERIFIABLE |

**8/9 findings abstain** in all modes. GROSS Cyrillic's explicit page-5 total is
now included despite its low retrieval rank; the old header/newer amount requires
contract-date and qualified legal review. It is not labelled an unlawful contract.
GROSS Latin has a damaged text layer; references do not establish explicit terms.
INSON's page-9 rules boundary was visually verified, with pages 9–66 correctly
classified as appendices. The historical inspection listing no appendices is stale
and retained as history. Its page-23 notification match is not reproduced as an
offer match by the current code. Every abstention's cause is in the audit report.

The read-only [baseline event comparison](audit_event_reproduction.json) confirms
two false matches caused by wrong event triggers are now abstentions. A newly
authored transfer-payment case changes from missed text to a potential conflict.
These are additional engineering regressions, not unexposed evaluation labels.

## Actual Chromium acceptance journeys

[Full browser record](audit_browser_results.json),
[date/mode smoke record](audit_smoke_results.json),
[actual missing-model fallback record](audit_fallback_results.json).

- Desktop 1365×950 and mobile 390×844; all three synthetic script variants,
  one newly authored four-page Russian transfer PDF, and the three original public
  PDFs. Unknown dates, historical 40-million reference and semantic/hybrid/lexical
  modes are exercised.
- On-screen summary and readable statuses match downloaded JSON; every quoted
  evidence item is verified against isolated extraction from the uploaded bytes.
- Two reviewer annotations are exported in HTML/JSON without changing findings.
  Script-like rationale renders as text, not active HTML. Another browser session
  cannot see the first session's report/reviews.
- Both dates, retrieval mode, upload replacement, clear, re-upload and empty new
  rationale fields are checked. Clearing actually resets browser configuration,
  in addition to server-side state.
- Finding evidence buttons open the expected raster page directly beneath the
  associated finding, with its exact quote and original page text. Coarse block
  geometry is not presented as exact highlighting.
- Exported HTML opens without external requests and prints through Chromium to
  an actual A4 PDF; expected amount and review text are extracted from the print.
  This validates HTML print-to-PDF; no runtime PDF-export dependency was added.
- Mobile horizontal overflow is **0 px** on the three script variants, the
  newly authored PDF and the opened evidence preview. Measured caption contrast
  is **7.06:1**, with an assertion of ≥4.5:1. No browser page errors
  or external application resource requests were observed.
- Screenshots of desktop, mobile, evidence and printed report pages were visually
  inspected. Artifacts: ignored `local_data/audit_browser/`; sample report:
  `reviewed.html`, print `reviewed-print.pdf`.

## Scope of assurance

The local app is working at localhost:8501. No hosting, production deployment,
new external AI API, rule expansion or legal approval was introduced. Review
identity is still a local demo label; OCR is unsupported. PyMuPDF distribution
licensing, qualified legal review, a broader unexposed evaluation, full accessibility
testing, hard Windows memory limits, durable authenticated reviews and rebuilding
the older Docker image remain future work. These limitations are not replaced by
the green local regression suite.

The late remote Dev Container addition (`987d3b7`) was preserved in a merge after
verification. It changes no benchmarked application source files and was not run.
Its disabled CORS/XSRF startup flags are recorded as an outstanding configuration
concern in the audit report; these results cover native localhost only.
