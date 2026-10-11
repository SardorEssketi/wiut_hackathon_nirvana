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

Baseline live runs also exposed an intermittent download timeout and downloads
without the expected saved review; these are recorded as failures rather than omitted.
The updated source uses explicit export widget identities per report, review
count and language. Strict post-change browser assertions still require the
actual downloaded JSON/HTML to contain the saved annotation. A later investigation
found that the original wait could match the editor's text before the save rerun,
so those failed journeys alone do not establish a persistent export defect.

Browser harness corrections: select the Cloud iframe instead of the gateway's
outer document; download diagnostics JSON instead of parsing the interactive JSON
tree; allow expected information alerts; wait for actual completed uploads and
saved review text; use a bounded 60-second Cloud download wait. None relaxes
finding statuses, legal abstentions, raster equality or export content assertions.
A local test process retaining old translation modules was restarted after the
translation edit, consistent with the documented source-update restart behavior.

## Final public Cloud verification

Source and observed deployed revision:
`39da0d50764273a08ca0c86e9eb936df1741376d`.
Cloud fingerprint:
`152a15b87225e695654d92afff2f0bf1157755006fd10514156e4f1cc49242c0`.
An independent hash over this commit's Git blobs matched the Cloud fingerprint.
Windows checkout CRLF bytes produce a different local fingerprint; compare
committed blobs or identical checkout line endings across hosts.

The strict actual Cloud Chromium journey **passed all four document scenarios**:

| Scenario | Confirmed date | Results | Actual retrieval |
| --- | --- | --- | --- |
| Synthetic exploratory review | None | 3 UNVERIFIABLE | lexical |
| Synthetic explicit conflicting terms | 2026-03-19 | 3 POTENTIAL_CONFLICT | lexical |
| Real GROSS Latin | 2026-03-19 | 3 UNVERIFIABLE | lexical |
| Real GROSS Latin exploratory review | None | 3 UNVERIFIABLE | lexical |

The synthetic comparisons were 60,000,000 versus 80,000,000 UZS, 9 versus 5
working days after the insurer's decision, and 20 versus 15 days after the written
indemnity request. These are engineering regression fixtures, not legal findings
against an insurer. GROSS's page-8 readability limitation and abstentions remain.

Additional assertions passed: one shared missing-date warning; three compact
pending rows with collapsed details; the date link does not itself confirm a date;
date/document/mode changes invalidate reports and selected evidence; no report or
image leaks into a fresh browser session; desktop/mobile have no horizontal
overflow; HTML/JSON share the explanations and original evidence; both exports
contain the actually saved, escaped review annotation; A4 print exposes pending
evidence; all three displayed synthetic highlight rasters exactly match the
validated worker output. The amount and both deadline highlights were also
visually inspected. The completed journey recorded **zero browser page errors**.

Machine-readable evidence: `evaluation/cloud_browser_results.json`.
Ignored full artifacts: `local_data/cloud_reboot_final_browser/`, including
`deployment.json`, `deployment-after-analysis.json`, `results.json`,
`pending-checks-desktop.png`, `unknown-mobile.png`, `conflict-desktop.png`,
`conflict-mobile.png`, three `*-verified-highlight.png` files and printed HTML.

The final review wait targets the saved `st.text` record in the analyst tab,
not the textarea or a duplicate note in another tab. It preserves the strict
download-content assertion. An intermediate selector incorrectly matched two
saved notes locally; it was scoped to the visible analyst tab and rerun
successfully locally and on Cloud. Two attempts during Cloud restart failed
before finding the app iframe; public gateway probes showed a waking/initializing
host rather than a completed application. No success is claimed for those runs.

## Actual AI availability and resource outcome

After the owner's corrected top-level secret was saved, live diagnostics confirmed
`operator_enabled: true`. After analysis, provisioning returned
`insufficient_or_unknown_memory_headroom`, with model files still absent.

- Actual Python: **3.14.8**.
- Actual packages: Streamlit **1.65.0**, CPU Torch **2.14.1+cpu**, PyMuPDF
  **1.28.2**, Pydantic **2.14.0**, sentence-transformers **6.1.0**,
  transformers **5.19.0**, NumPy **2.5.4**.
- Cgroup limit: **3,221,225,472 bytes (3 GiB)**.
- Post-analysis cgroup usage: **2,151,600,128 bytes**; provisioning snapshot
  usage: **2,151,608,320 bytes**. Remaining budget was about **1020 MiB**, below
  the required **1536 MiB** headroom. Observed peak: **2,836,746,240 bytes**.
- `cpu.max`: **max 100000**; no hard CPU quota is exposed by this cgroup file.
- Both parent offline flags remain **1**, threads setting **2**.

No model download was attempted under this budget. All four actual reports
explicitly record `retrieval_used: lexical` and `model_revision: null` while the
UI states **without AI**. The measured cgroup usage includes more than application
RSS and may include file cache/other processes; these measurements establish the
conservative gate refusal, not a demonstrated model OOM or permanent impossibility
on every free host. Successful provisioning or E5 inference on this Cloud host
remains **unverified**. Private owner/build logs remain unavailable.

The final committed-source local journey passed the same four scenarios with
actual **hybrid** retrieval and E5 revision
`614241f622f53c4eeff9890bdc4f31cfecc418b3`:
`local_data/cloud_harness_final_local_browser/results.json`.
The separate multilingual local browser suite passed **9 UI/document-script
combinations** plus language-switch/review preservation, mobile isolation and
A4 exports; metadata is `evaluation/cloud_i18n_browser_results.json`.
An additional actual **Russian Cloud GROSS Latin unknown-date journey passed**:
one shared warning, three compact pending checks, desktop/mobile without overflow,
consistent HTML/JSON and no invented evidence locations. This run retrieved zero
qualifying quotations, so it does not demonstrate a GROSS PDF highlight. The
nine local script combinations verify preservation of nonempty multilingual
quotations. Russian screenshots are in `local_data/cloud_russian_browser/`.
Its first attempt timed out during the 2.2 MB upload at 30 seconds; the repeat
waited up to 120 seconds for a completed upload and passed. Parsing/rendering
timeouts and resource limits were unchanged.
The numerical engine, legal catalogue and exact localization code were not
changed by this Cloud-readiness release. OCR, expert legal certification,
concurrent peak-load safety and successful Cloud model loading are not claimed.

## Changed files and reproducible checks

Application: `app.py`, `polisdiff/deployment.py`, `polisdiff/provisioning.py`,
`polisdiff/runtime.py`, `polisdiff/retrieval.py`, `polisdiff/presentation.py`,
`polisdiff/readiness_copy.py`, `polisdiff/i18n.py`, `polisdiff/export.py`,
`requirements.txt`, `scripts/download_model.py`.

Verification: `tests/test_app_startup.py`, `tests/test_cloud_provisioning.py`,
`tests/test_readiness.py`, `scripts/browser_cloud_readiness_check.py`,
`scripts/browser_cloud_russian_check.py`, `scripts/browser_i18n_check.py`,
`evaluation/cloud_browser_results.json`, `evaluation/cloud_i18n_browser_results.json`,
`evaluation/cloud_russian_browser_results.json`.

Documentation: `docs/CLOUD_READINESS.md`, `docs/FINDING_EXPLANATIONS.md`,
`evaluation/CLOUD_RESULTS.md`. Unrelated `docs/TEAM_BRIEFING.md` was preserved.

Commands (use the local Python environment with the existing browser-test tools):

```powershell
.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/cloud_source_final_tmp --junitxml=local_data/cloud_source_final.xml
.venv/Scripts/python.exe scripts/browser_cloud_readiness_check.py --url https://polis-diff-ai.streamlit.app/ --name cloud_reboot_final_browser --expected-revision 39da0d50764273a08ca0c86e9eb936df1741376d
.venv/Scripts/python.exe scripts/browser_cloud_readiness_check.py --url http://127.0.0.1:8514 --name cloud_harness_final_local_browser --expected-revision 39da0d50764273a08ca0c86e9eb936df1741376d
.venv/Scripts/python.exe scripts/browser_i18n_check.py --url http://127.0.0.1:8514 --output cloud_i18n_browser_results.json --artifact-dir local_data/cloud_i18n_browser
.venv/Scripts/python.exe scripts/browser_cloud_russian_check.py
```

The final verification commit changes documentation, browser harnesses and result
records only. The application content tested locally and on Cloud remains that
of `39da0d5`; no new engine edits followed the 540-test full suite.
