# Evidence, explanation and correction workflow

This workflow screens **three OSAGO conditions**, not whole-document legality.
Every interpretation remains `PENDING_LEGAL_REVIEW`. A potential conflict is an
engineering comparison requiring qualified legal review, never a certified violation.
The deterministic engine, rule catalogue, retrieval and date selection are unchanged.

## Explanation sources

`polisdiff.presentation.finding_details(report, finding, language)` supplies both
Streamlit and the self-contained HTML report. It combines recorded evidence,
extracted values/units, status, reason, uncertainty, applicability dates and the
selected legal-source quotation/version. Fixed copy is translated through the
existing four-language catalogue; documentary/legal quotations and version notes
remain in their original language. No LLM, external AI API or new legal requirement
is used. Source quotations are the catalogue's narrow verified excerpts, not a
substitute for inspecting the complete official provision and its context.

Each result has a scope, observation, reference, reason, original evidence/pages,
verification checklist, conditional action, verification state and legal-review
notice. A numeric correction recommendation requires an offer term with the
appropriate unit, an applicable recorded version and date, a source quotation,
and no recorded ambiguity. All competing/uncertain terms remain visible. Dates
confirmed by a user are expressly distinguished from review of primary documents.

The UI has five summary counts, compact findings with direct PDF actions, and
expandable evidence/resolution columns. Potential conflicts appear first. Desktop
shows original evidence alongside the legal reference and resolution; narrow
screens stack them. JSON and offset details remain in technical expanders.
Reviewer records remain annotations and never override the engine result.

## Precise localization

1. Reconstruct the selected page with the **same sorted PDF-block extraction**
   protocol as `extraction._extract`. Evidence offsets are page-relative, not
   offsets into normalized search text. Verify the exact original quote at those
   offsets and its passage/document identity. Empty or stale evidence is rejected.
2. Re-run the existing numeric extractor against the quote and verify its recorded
   value/unit. Locate the unique monetary expression or deadline using the existing
   rule regex. An explicit reversible map permits whitespace and Uzbek apostrophe
   differences. Other lossy normalization, altered numbers, missing values and
   ambiguous numeric expressions abstain. The amount includes its stated currency
   and any parenthesized amount wording; deadlines include their day unit/modifier.
3. Read PyMuPDF `rawdict` spans/characters for **only the selected page**. Join each
   original block to a unique character block by its matching boundary and full
   reconstructed text, allowing only the same whitespace/apostrophe equivalence.
   **Block numbers are not stable across these APIs when images are present.**
4. Map the exact original substring to character boxes. Keep distinct lines and
   large gaps separate; never paint a passage/block union. Require horizontal
   character direction, finite nonempty boxes inside the page and independent
   word geometry. Reject duplicated overlaid words and ambiguous block joins.
5. Paint a translucent rectangle over each validated character run in a temporary
   worker-owned PDF object, then rasterize it. Page rotation is handled by PyMuPDF's
   rendering transform; geometry stays in original page coordinates. The uploaded
   PDF bytes are never modified. Streamlit uses lossless PNG output.

Repeated values elsewhere cannot redirect the highlight: page-relative evidence
offsets select the original block/substring before any geometry is considered.
Columns/tables are supported only when that entire mapping validates; no reading
order is inferred from numeric search results. Section/paragraph numbers are not
invented. The original `Evidence.bbox` remains a coarse provenance field only.

If the exact character mapping fails, show the supported page and original quote,
mark the substring in the text view only if its reversible mapping validates, and
state **“Precise PDF highlighting is unavailable.”** Evidence with no numeric
extraction (unknown dates, appendices, references, etc.) still opens its actual
page, but does not receive a guessed numeric highlight. No evidence means no PDF
action and no claimed location. Manual page navigation remains an explicit user
action independent of findings.

## Corrective recommendations and abstention

| State | Verification and action |
| --- | --- |
| `POTENTIAL_CONFLICT` | Show the actual/reference difference and applicable event. Verify date, scope, legal version, units, trigger and full clause context. Only after these checks may a specialist consider reviewing the total amount, payment deadline or notification deadline for correction. |
| `MATCH_FOUND` | The specific checked criterion is consistent. Recommend no change for that criterion; do not approve the whole document. |
| `NOT_FOUND` | Check remaining pages, appendices and incorporated documents. Do not invent a missing clause's location or an obligation to insert disclosure language. |
| `UNVERIFIABLE` | Show the recorded blocking reason(s). Confirm an unknown date, obtain the historical version, inspect competing amounts/events/units, review incorporation, or obtain readable source text as appropriate. Do not recommend editing the contract on this result. |

The sum checklist distinguishes total coverage from premium, sublimits and
examples. Payment requires working days measured from adoption of the insurer's
indemnity decision. Notification requires the correct recipient and a written or
electronic indemnity-request trigger; it is not a generic decision-taking deadline.
These are the existing catalogue interpretations, all pending legal review.

Unreadable-page findings request a readable text PDF or manual original inspection:
**technical remediation is not contractual remediation**. OCR remains unsupported.
Copied regulatory appendices do not prove explicit offer commitments. Incorrect
events and competing values remain abstentions. A historical public-document
scenario does not prove that date governs the actual document.

## Amendment drafts

The optional draft feature was investigated and deliberately omitted. Existing
reports record user-confirmed dates, not independently verified documentary date
support, complete incorporation/transition context, or qualified legal approval.
Consequently `finding_details` returns `draft=None` and a rule-specific checklist.
There is no free-form legal generator and no automatic PDF editing. This preserves
the original quotation and avoids an apparently approved replacement provision.

## Security, export and compatibility

PDF parsing/rendering remains in killable subprocesses. Extraction retains the
25-second timeout and 10 MiB / 80-page / 500,000-character / 1,800-passage limits.
Evidence rendering retains a 15-second timeout and a 1,400-pixel longest-edge cap;
Linux workers retain CPU/address-space limits. The PDF/evidence envelope is bounded
and travels on stdin, not disk or logs. Only one preview is kept in session RAM,
keyed by document, page, finding and evidence. Changing inputs or evidence clears
the previous selection/preview. No global document cache or all-page renderer is
introduced. Windows still lacks a verified hard worker memory cap.

HTML contains the same explanations, original quotations, page numbers, values,
date/version notes, conditional actions, source links and legal-review notice.
All source/reviewer text is escaped; source URLs retain the official HTTPS LexUZ
allowlist. It uses local CSS, A4 print styling, no scripts/fonts/CDNs, and no PDF
images or highlights. PDF geometry is ephemeral and is recomputed from original
bytes; it is never trusted from exported JSON. **No model/schema change was
needed**: old schema-1.0 reports remain readable and optional old fields retain
their defaults. Explanations are derived on demand rather than persisted twice.

## Verification and limitations

Commands and fresh measurements are recorded in `evaluation/FINDING_RESULTS.md`.
`tests/test_finding_workflow.py` covers original-text geometry, duplicate values,
multiline amounts, 0/90/180/270-degree pages, columns/tables, images changing block
identifiers, apostrophes, Uzbek Cyrillic/Russian, damaged/unsupported evidence,
appendices, historical/unknown dates, wrong events, competing values, every
rule/status guidance combination, old JSON, malicious text and stale selections.
Existing tests are retained. Browser selectors were updated for the new PDF
action and nested evidence hierarchy without removing assertions.

`scripts/browser_finding_check.py` exercises real Chromium desktop/mobile flows,
compares displayed raster pixels with the validated worker output, checks
annotations, isolation, source data/HTML agreement and actual A4 printing.
`scripts/browser_i18n_check.py` retains the four-language switching and nine
document-script/language journeys. `scripts/verify_finding_geometry.py` produces
selected page images for manual visual review; offset equality alone is insufficient.

Known limits: OCR/scans, damaged font encodings, arbitrary normalization repairs,
vertical/oblique text (distinct from rotated pages), duplicate/overlapping text,
unvalidated table/column order, complex event paraphrases, historic transition
interpretation and independently proven contract dates. Mapping failure is a
localization limitation and does not change the finding's legal/evidence status.
The public samples remain engineering evidence scenarios, not legal ground truth.
No public deployment, Docker rebuild, expert legal validation, full accessibility
audit or first-time-user study is claimed.

## Restart after a hosted source update

Streamlit can rerun the updated entry point while Python still holds imported
modules from the preceding release. An import error naming `render_evidence`
despite that function being present in the pushed `extraction.py` is reproducible
with the preceding extraction module retained in `sys.modules`. Retaining the
older presentation module likewise prevents importing `finding_details`.

Startup checks for these APIs before importing them and shows a restart message
instead of a traceback when they are missing. This check does not reload shared
modules or allow an analysis using mismatched versions. The app owner must use
**Manage app → Reboot app** on Streamlit Community Cloud, or restart a local
Streamlit server. A browser refresh alone does not restart Python. Active
session uploads and unexported annotations are held in memory and are lost on
server restart; export them before a planned update. Fresh-process startup and
both stale-module cases are covered by `tests/test_app_startup.py`.

On 2026-10-11 the regression reproduced three startup failures before the guard
(extraction, presentation, both), with fresh startup passing. After the change,
all four startup tests passed and the full suite passed **509 tests in 54.77s**.
Actual Chromium desktop/mobile startup passed with zero page errors; screenshots
and results are in ignored `local_data/startup_browser/`. These checks used local
Python 3.12.6; the hosted Python 3.14 process and its reboot were not accessible
or verified. The first browser probe incorrectly rejected expected informational
alerts; it was corrected to check exceptions, error alerts and the restart
message specifically, then passed.
