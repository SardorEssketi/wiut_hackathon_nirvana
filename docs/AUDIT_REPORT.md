# PolisDiff AI engineering and UX audit

Audit date: 10 October 2026. Baseline checkout: `41dcafd` on `main`, with a clean
working tree and the requested GitHub remote. The active local files were read
before editing; no local work was reset or discarded. This audit covers the
native Streamlit application, not a new production deployment or Docker release.

All legal interpretations remain **PENDING_LEGAL_REVIEW**. The rule catalogue,
its reference values and its three-check scope were not changed. Engineering
trigger recognition and candidate selection changed; they are not legal approval.

## Fresh evidence and reproduction

The original suite was executed before pipeline changes: **67 passed in 27.11 s**.
Baseline JUnit is in ignored `local_data/audit_baseline_tests.xml`; its sanitized
count record is `evaluation/audit_baseline_tests.json`. All three benchmark modes
were reproduced into a separate directory. The reproduced hybrid former-fresh
accuracy was **8/9 = 88.9%**, with **4/5 = 80% conflict recall**, matching history.

New independent regression tests initially produced **7 failures / 4 passes**:
two transfer-verb misses, three unsafe extraction decisions, a request-trigger
error and stale embeddings after `prepare([])`. These failures were fixed without
changing existing expected statuses. A first strict notification grammar change
failed existing Russian tests; the missing possessive/alternative wording was
corrected and the original assertions retained.

Current outcomes and raw artifacts are in [AUDIT_RESULTS.md](../evaluation/AUDIT_RESULTS.md).
Original `benchmark_results.json`, original synthetic per-case reports,
`real_extraction.json`, historical test files and fixture PDFs are preserved.
Formerly fresh fixtures now influenced the fixes and are explicitly **regression
data**, not an untouched holdout. Newly authored tests are also engineering
regressions, not independent expert validation.

Commands (PowerShell, with existing `.venv` and locally provisioned model):

```powershell
.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/audit_release_tmp --junitxml=evaluation/audit_tests.xml
.venv/Scripts/python.exe scripts/test_summary.py evaluation/audit_tests.xml
.venv/Scripts/python.exe evaluation/benchmark.py --output-dir local_data/audit_post_verified --label post-audit-regression
.venv/Scripts/python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501
# Keep Streamlit running for these actual Chromium checks:
.venv/Scripts/python.exe scripts/browser_check.py
.venv/Scripts/python.exe scripts/local_smoke.py
.venv/Scripts/python.exe scripts/browser_fallback_check.py
.venv/Scripts/python.exe scripts/audit_public_samples.py
.venv/Scripts/python.exe scripts/audit_event_regression.py
```

The public-sample script requires the original ignored PDFs identified by
`evaluation/source_manifest.json`. It stores full text, screenshots and reports
only in `local_data/audit_public/`; the checked-in result contains causes/pages,
not insurer quotations. The fallback script starts and stops its own loopback
server with an intentionally absent model. No hosting or external AI API is used.

## Confirmed issues

### High — incorrect event attribution can accept the wrong deadline

File: [engine.py:79](../polisdiff/engine.py#L79), notification parsing at line 87.

Observed behavior: the old extractor accepted any `после принят…` prefix while
finding `решение` anywhere in the passage. A 4-working-day payment after a court
decision or acceptance of an application could therefore satisfy an insurer-
decision check when a recognized payment verb was used. Notification extraction
also accepted a written request mentioned elsewhere, even when the actual deadline
ran from an accident.

Reproduction: test the court/application examples in
`test_transfer_wrong_trigger_or_negation_abstains` with `выплачивается`, and
`test_request_mentions_are_not_notice_trigger`. `extract_value()` previously
returned no abstention reason. The full court-PDF regression now asserts
`UNVERIFIABLE`, rather than `MATCH_FOUND`.

Root cause: event keywords were not grammatically associated with the trigger.
Fix: Russian adoption must directly identify the insurer's decision; notification
must link the written/electronic request to an explicit temporal phrase. Supported
possessive/alternative and Uzbek trigger forms remain tested. Negation and
conditional cases abstain. Remaining limitation: unsupported paraphrases and
complex interleaved events can still require abstention; no general language
understanding or expert legal interpretation is claimed.

The read-only baseline comparison in `audit_event_regression.py` evaluates newly
authored PDFs against both the inspected `41dcafd` engine and the current engine,
without checking out or resetting files. The stored
`evaluation/audit_event_reproduction.json` confirms court and accident-trigger
cases changed from MATCH_FOUND to UNVERIFIABLE, and the transfer case changed
from NOT_FOUND to POTENTIAL_CONFLICT.

### High — top-K ranking can omit a real or competing contractual value

File: [service.py:36](../polisdiff/service.py#L36).

Observed behavior: the actual GROSS Cyrillic PDF contains an explicit total on
page 5. Hybrid top-eight retrieval omitted the passage, while an exhaustive
topic/extractor probe recognized 80,000,000 UZS. A ranking omission can also hide
a contradictory value and produce an unjustifiably confident match.

Root cause: only ranked candidates were passed to deterministic evaluation.
Fix: after separate offer/appendix retrieval, all recognized topic passages in
the offer are admitted, deduplicated by passage ID. The engine still applies all
date, scope, unit and ambiguity checks. It never upgrades appendix text to an
offer commitment. `candidate_selection` records this guard in JSON and HTML.

Proof: `test_retrieval_does_not_hide_competing_offer_value` simulates a ranker that
returns only the matching page; the contradictory page is included and evaluation
abstains. Public page 5 now produces a potential conflict for the explicitly
selected 2024 applicability scenario. That sample has an old header/newer amount,
so legal/date review remains necessary. The guard covers recognized topics;
neither retrieval nor its guard guarantees complete document coverage.

### Medium — missed Russian transfer payment wording

File: [engine.py:37](../polisdiff/engine.py#L37).

Observed behavior: `перечисляется` was retrieved correctly but rejected as a
payment topic, producing `NOT_FOUND` for a 7-working-day term in the former-fresh
Russian case. Root cause: a limited payment-verb vocabulary.

Fix: add narrow finite transfer verbs, with the same event/unit/date checks and
explicit negation protection. Nominal wording such as `о перечислении` in a notice
is not recognized as an actual payment event. Tests:
`test_russian_transfer_payment_independent` (new 3- and 9-day cases),
`test_notice_of_transfer_is_not_payment`, wrong-trigger/negation/condition cases,
and the full benchmark. Original failed fresh measurements remain historical;
post-fix 9-label results are regression measurements only.

### Medium — mutable retriever state was cached across browser sessions

Files: [app.py:86](../app.py#L86), [runtime.py:15](../polisdiff/runtime.py#L15),
[retrieval.py:80](../polisdiff/retrieval.py#L80).

Observed behavior: the previous `st.cache_resource` returned a mutable retriever
per mode across sessions, and `prepare([])` retained previous embeddings. The
analysis semaphore and finally cleanup mitigated mixing; **no cross-session data
leak was observed**. The shared mutable state nevertheless created retention and
future concurrent-use hazards. The previous shallow runtime copy also shared its
query dictionary. `lru_cache` alone could duplicate first initialization under
contention.

Fix: cache only the base model; create a fresh retriever per analysis, copy the
static-query dictionary, reset embeddings on every prepare, serialize model
initialization, and retain finally cleanup. Tests:
`test_prepare_empty_clears_embeddings`,
`test_runtime_retrievers_do_not_share_query_or_document_state`, the existing
shared-model test, actual offline-model tests, timeout/gate cleanup, and independent
browser-session analysis. Remaining limit: one active analysis per process;
the cached model is substantial and has no production throughput guarantee.

### Medium — optional model provenance could disagree with actual execution

File: [retrieval.py:57](../polisdiff/retrieval.py#L57).

Observed behavior: a manifest read/key failure after model loading entered the
fallback exception path while leaving `model` non-null. Search could still execute
embeddings while reporting lexical mode. A custom model path also inherited the
default manifest's revision without comparing files.

Fix: optional provenance errors leave a loaded model's actual mode intact; a
failed model load clears the model before lexical fallback. Report the recorded
revision only when critical config, weights, tokenizer and pooling hashes match.
Offline/telemetry flags are enforced and loading remains local-only with
`trust_remote_code=False`. Tests: missing-model fallback, mocked bad-manifest
loaded-model test, network-blocked real embeddings, and the real fallback browser
server. Remaining limit: this is provenance metadata, not signed supply-chain
attestation or tamper-proof model storage.

### Medium — session clear and new review forms could retain browser widget state

Files: [app.py:38](../app.py#L38), [app.py:135](../app.py#L135),
[session.py:11](../polisdiff/session.py#L11).

Observed behavior: an actual browser journey switched to semantic mode, cleared
the session and re-uploaded a file; the mode remained semantic despite deletion
of server state. Reusing the same form widget identities also risked restoring
an old rationale on a different analysis. Root cause: browser widget identity was
stable even after deleting session keys.

Fix: assign new upload/configuration keys after clearing, key review forms and
manual page controls to document hash plus report creation time, invalidate results
on any document/date/mode change, and discard a previous result before a failed
reanalysis. Unit tests cover fingerprint changes, retained reruns and page selection.
Chromium checks exercise A→review/export→B, both dates, modes, another annotation,
clear/re-upload, empty new rationale fields, and another browser session. Records
remain local annotations; no authentication, qualified identity or durable store
was introduced.

### Medium — unsupported dates retained an inapplicable numeric reference

File: [engine.py:117](../polisdiff/engine.py#L117).

Observed behavior: unsupported/future/audit-order-invalid dates already abstained,
but could retain the current version's expected value and source quotation in the
finding. This risked presenting that version as the applicable numerical target.
Root cause: source selection happened before the supported-date check.

Fix: clear the selected target/period/quote on unsupported dates; keep the generic
official link and abstention reason. Contract input now starts empty and an unknown
date warning appears before running. Tests cover unknown, early, future and
audit-order-invalid dates, plus historical 40-million applicability in Chromium.
Unresolved transition treatment stays PENDING_LEGAL_REVIEW.

### Medium — reports exposed status codes instead of a readable review

Files: [presentation.py:8](../polisdiff/presentation.py#L8),
[export.py:52](../polisdiff/export.py#L52), [app.py:136](../app.py#L136).

Observed behavior: raw enum/reason/metadata dominated the report and UI; extracted
numbers in reasons could use scientific notation. Evidence navigation was a
separate manual page selector. Root cause: no shared presentation layer or report
information hierarchy.

Fix: shared deterministic Russian labels, count summaries, readable amounts,
scope/observation/reference/reason/evidence/next-step cards; exact-page raster
navigation directly beneath the associated finding; self-contained executive
summary, overview, detailed findings, review
records, limitations and late technical appendix. JSON retains original enums and
reasons, with additive metadata and historical JSON readability. All 64 status
combinations are tested; UI and HTML use the same explanation functions. Browser
downloads compare statuses/reviews, original quote offsets, summary and A4 output.
Remaining limit: Russian is the initial UI language; document quotations retain
their original language and are never replaced by translations.

### Low — escaped source URLs could still use an active unsafe scheme

File: [export.py:17](../polisdiff/export.py#L17).

Observed behavior: HTML escaped strings but inserted any `source_url` into an
anchor. A programmatically imported report with `javascript:` could create an
active link. The trusted catalogue did not expose this through the upload UI.
Root cause: HTML escaping does not validate URL schemes.

Fix: allow HTTPS LexUZ on the standard port; malformed, data, javascript and
deceptive-host links become plain text. Escaping is retained for all document and
review content; CSP blocks scripts, network assets and forms. Tests cover malicious
quotes/reviews, five unsafe/malformed URLs, Unicode and long strings. The browser
opened the exported HTML with zero external requests and printed it to A4.
No claim of enterprise security follows from these checks.

### Low — caption opacity reduced readability

File: [app.py:24](../app.py#L24).

Observed behavior: Streamlit's caption container retained opacity 0.6 even after
setting a darker text color. Date guidance, source context and retention notes
appeared lighter than intended. Root cause: inherited container opacity blended
the configured color with the background. Fix: render captions at full opacity,
retain a restrained dark slate color, and preserve visible keyboard focus styles.
Chromium computes the effective caption/background contrast and asserts at least
4.5:1; desktop and mobile screenshots are visually inspected. This is a targeted
contrast/layout review, not complete WCAG or screen-reader certification.

### Low — stale INSON appendix inspection conflicted with active behavior

Files: historical `evaluation/real_extraction.json`; current
[extraction.py:57](../polisdiff/extraction.py#L57).

Observed behavior: the historical file lists no appendix pages and one match from
page 23. Current isolated extraction classifies pages **9–66** as appendices.
Original page 8 ends the offer with insurer particulars; page 9 visibly contains
a rules heading and attribution to appendix 4 of Resolution 141. The source bytes
match the recorded SHA-256.

Root cause: the old inspection was not regenerated after an earlier extractor
fix. **No current appendix-classification defect was reproduced on INSON.**
Fix: preserve history, label it stale in documentation, record a fresh separate
inspection, and add an original-sample check plus a synthetic split-heading
appendix regression. The current page-23 notification is not counted as an offer
match. Remaining limit: boundary detection is heuristic and persists after a
recognized rules boundary; unseen layouts still need manual review.

## Every public-sample finding

These are engineering observations under explicitly selected applicability
scenarios from `real_annotations.json`, not expert-labelled legal ground truth.
Original pages were rendered and visually inspected. Full quotes stay local.

| PDF / check | Current result | Actual cause and evidence |
| --- | --- | --- |
| GROSS Latin / total | UNVERIFIABLE | Page 6 visually has a total, but the extracted layer mixes Latin/Cyrillic lookalikes and malformed `summэsi`/currency/digits. No supported exact amount was extracted; page 1 incorporates rules by reference. OCR is absent. |
| GROSS Latin / payment | UNVERIFIABLE | No complete explicit insurer-decision payment deadline was extracted anywhere in the offer. Page 1 references rules; damaged text prevents concluding the original clause is absent. |
| GROSS Latin / notification | UNVERIFIABLE | No supported explicit notification deadline/trigger was extracted; page 1 reference plus damaged text. A missing-document finding would overstate available evidence. |
| GROSS Cyrillic / total | POTENTIAL_CONFLICT | Page 5 clause 30 explicitly states 80,000,000 UZS. The selected 2024-09-06 scenario uses the catalogue's 40,000,000 reference. Earlier hybrid top-K omitted this clause. The old header/newer amount makes contract-date verification essential. |
| GROSS Cyrillic / payment | UNVERIFIABLE | Page 4 is a right to challenge a refusal and obtain compensation, with no qualifying deadline. No fully extracted offer payment deadline exists; relevant rules are referenced rather than fully stated. |
| GROSS Cyrillic / notification | UNVERIFIABLE | References on pages 1 and 5; no complete supported offer notification term. Page 5's 3-working-day missing-document notice is a different event and is not treated as the fifteen-day decision notice. |
| INSON / total | UNVERIFIABLE | Page 5 contains a visually readable total with sublimits; extracted amount has letter O / damaged digits and adjacent partial-limit context. No complete supported total is extracted. Letters are never silently converted to zero. |
| INSON / payment | UNVERIFIABLE | Offer page 4 is a right to appeal refusal, not a deadline. The recognizable five-working-day payment clause is on page 23 in the statutory appendix. It cannot establish the insurer's own explicit offer commitment. |
| INSON / notification | UNVERIFIABLE | A full notification term appears on appendix page 23 only. Section attribution prevents a match based on copied regulatory text. |

All modes are remeasured; the public sets have no legal-status labels. Eight of
nine findings remain unverifiable. No unsupported recovery of damaged text,
invented compliance label or replacement of a real result with synthetic success
was used.

## Systematic checks and remaining constraints

PDF parsing: header/size/page limits precede inference; malformed/encrypted/scan
cases, unsupported page indices, isolated-worker timeouts and gate cleanup are
tested. Original offsets are checked against the page text on every benchmark
evidence item and all seven browser inputs. Native extraction is bounded by
25-second timeouts, 80 pages, 500,000 characters and 1,800 passages. Raster preview
has a 15-second timeout and a 1,400-pixel longest-edge bound. Windows has no verified
hard process memory cap, and the text limit applies after native page extraction;
resource/decompression hazards are not eliminated. Geometry is a block union, so
no inaccurate quote highlighting was added.

Retrieval: actual offline E5 embeddings are exercised with sockets blocked; browser
requested/actual modes agree, including a missing-model lexical fallback. Query
caching contains catalogue queries only. Ranking uses at most 512 tokens per
passage; original evidence remains complete and the offer-topic guard reads it.
Memory/latency are machine-specific measurements; no AI precision advantage or
production capacity claim is established.

Rules: numeric separators, UZS context, property/premium exclusions, working versus
ordinary days, competing values, reference incorporation, conditional/negated
terms, unsupported dates and historical versions retain conservative checks.
Unseen language, tables and unusual event syntax remain limitations. The source
catalogue's engineer-authored interpretations require qualified legal review.

State/export: reviews do not change findings; invalid review actions/rationale
lengths are rejected atomically. Config changes, re-upload, failed analysis and
clear are isolated from previous reports. HTML uses no scripts, remote fonts or
CDNs and prints to A4. JSON keeps existing fields/enums. Exports remain on the
analyst's device; clearing session RAM is not verified secure erasure.

Security/privacy/licensing: common GitHub/AWS token and private-key signature
searches across tracked history returned no matches; `.env`, Streamlit secrets,
weights, virtual environment and public PDFs are excluded from Git. This is not
an exhaustive secret-detection or penetration test. Server logs inspected during
the run contained startup/model/library notices, not uploaded quotations or
review rationale. Browser journeys made no external resource requests. No
confidential inputs, external AI service or production hosting were introduced.
PyMuPDF's official [licensing documentation](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright)
continues to describe AGPL and commercial options; distribution/hosting obligations
and the original-code licence decision remain unresolved. This audit does not
certify licence compliance.

No Critical vulnerability was demonstrated in this bounded local audit. That does
not establish absence of critical defects. A real first-time-user usability study,
screen-reader audit, broader unexposed multilingual evaluation, OCR validation,
qualified legal review, durable authenticated reviews, Windows memory enforcement
and a fresh Docker build remain outside the verified outcome. The local app and
its browser/export journeys are the delivered scope.
