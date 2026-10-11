# Cloud readiness verification — 2026-10-11

Baseline checkout: `04459a54c641ce5b7c418ec12e50ccc9a958ae82`.

- Baseline suite: **509 passed in 53.39 s**.
- Affected presentation/startup/export suite: **334 passed in 6.94 s**.
- Readiness + affected suite: **350 passed in 8.65 s**.
- Intermediate full suites: **536 passed in 44.24 s**, then **538 in 54.08 s**.
- Final full source suite: **540 passed in 54.56 s**; 31 additional regression
  cases, zero failures/errors/skips. JUnit: ignored
  `local_data/cloud_source_final.xml`.

Actual local Chromium completed unknown/supported dates, three synthetic conflicts,
GROSS Latin with/without a date, original GROSS abstentions, desktop/mobile without
overflow, actual hybrid E5 execution and pinned model revision, rendered raster
pixel equality, exact marked phrases, HTML/JSON shared explanations, escaped
annotations, session isolation and date/document/search-mode invalidation. A4
printing exposes the evidence inside screen-collapsed unknown-date details.
Artifacts: `local_data/cloud_local_final_browser/` and its `results.json`.
Those runs used Windows Python 3.12.6. They are not claims about Cloud execution.

The public deployed app at `https://polis-diff-ai.streamlit.app/` was exercised
through its actual Cloud iframe, not an imitation on localhost. The pre-change
version produced three abstentions without a date and three expected synthetic
potential conflicts for the supported 2026-03-19 scenario. Actual retrieval was
`lexical` despite requesting `hybrid`; reports recorded `FileNotFoundError` and
no model revision. Displayed highlights matched the independently validated
worker pixels for all three synthetic rules. Private owner/build logs were not
available and this release had no public revision diagnostics yet, so its exact
deployed Git SHA was not established solely from those reports.

Baseline live runs also exposed an intermittent download timeout and repeated
stale review exports; these are recorded as failures rather than omitted.
The updated source uses explicit export widget identities per report, review
count and language. Strict post-change browser assertions still require the
actual downloaded JSON/HTML to contain the saved annotation.

Browser harness corrections: select the Cloud iframe instead of the gateway's
outer document; download diagnostics JSON instead of parsing the interactive JSON
tree; allow expected information alerts; wait for actual completed uploads and
saved review text; use a bounded 60-second Cloud download wait. None relaxes
finding statuses, legal abstentions, raster equality or export content assertions.
A local test process retaining old translation modules was restarted after the
translation edit, consistent with the documented source-update restart behavior.

The post-push source/deployed revisions, final live outcomes, resource budget and
remaining limitations will be appended after verification of the updated host.
