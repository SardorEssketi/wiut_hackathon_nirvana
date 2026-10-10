# Actionable findings verification

Executed locally on 10 October 2026 from `ac2ca23`, including the earlier
`3dcfe7d` audit and subsequent multilingual UI commits. Initial status contained
only untracked `docs/TEAM_BRIEFING.md`; that file was not changed or committed.
No deployment, remote push, catalogue interpretation or analysis status change
was performed. All interpretations remain **PENDING_LEGAL_REVIEW**.

## Automated results actually executed

| Run | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Current-checkout baseline, workspace temp directory | 459 | 0 | 0 | 0 |
| Initial affected tests | 405 | 1 | 0 | 0 |
| First complete post-change run | 499 | 0 | 0 | 0 |
| Final dedicated workflow suite | 46 | 0 | 0 | 0 |
| Final complete suite | **505** | **0** | **0** | **0** |

The earlier 175-test engineering audit is preserved. The latest checkout had
459 tests because it also included multilingual regression cases; all remain
passing. The final run took **53.58 seconds**, adding **46 dedicated tests**.
Counts are executed test cases, not new tests multiplied by repeated runs.

Before the successful baseline, the default Windows pytest temp directory caused
15 fixture-setup permission errors (444 passed). Rerunning with a fresh directory
inside `local_data` resolved the environment issue; no assertion was changed.
The affected-suite failure discovered that the shared fixture builder folded a
requested newline into a space. Its replacement draws two actual PDF lines and
retains the two-box assertion. Later geometry work added separate tests for
duplicate overlaid text, oblique text, damaged evidence and image-induced block
identifier differences. Existing tests were not weakened.

Fresh machine-readable counts/JUnit: `finding_baseline_tests.json/.xml`,
`finding_affected_tests.json/.xml`, `finding_tests.json/.xml`. Intermediate
499-pass and dedicated 46-pass outputs were observed directly during execution.

```powershell
.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/finding_baseline_tmp --junitxml=evaluation/finding_baseline_tests.xml
.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/finding_release_tmp --junitxml=evaluation/finding_tests.xml
.venv/Scripts/python.exe scripts/test_summary.py evaluation/finding_baseline_tests.xml
.venv/Scripts/python.exe scripts/test_summary.py evaluation/finding_tests.xml
.venv/Scripts/python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8512
```

## Chromium and visual verification

`finding_browser_results.json` records the new review journey. It verifies all
three synthetic potential conflicts with correct original pages, exact marked
quotes, displayed raster pixels equal to the bounded worker output, desktop
1365×950 and mobile 390×844 layouts, original reviewer annotations, JSON/HTML
explanation consistency, unknown-date abstention, no invented location/action
for absent evidence, wrong-event abstention, stale-input invalidation, session
isolation and actual A4 print-to-PDF. HTML/script-looking evidence and reviewer
text remain literal escaped text. No browser page errors or external application
resource requests were observed on successful runs.

`finding_i18n_browser_results.json` records the existing nine document-script/UI
language combinations, desktop/mobile navigation, switching all four languages
without altering reports or reviews, unknown dates, session-local preferences and
three A4 language exports. The prior `i18n_browser_results.json` is preserved.
`finding_native_browser_results.json` records the existing full native audit:
seven real/synthetic inputs, offline AI retrieval, dates/modes, human annotations,
clear/re-upload, independent sessions, mobile evidence and A4 HTML printing.

Reproduction (while the loopback server is running):

```powershell
.venv/Scripts/python.exe scripts/browser_finding_check.py --url http://127.0.0.1:8512
.venv/Scripts/python.exe scripts/browser_i18n_check.py --url http://127.0.0.1:8512 --output finding_i18n_browser_results.json --artifact-dir local_data/finding_i18n_browser
.venv/Scripts/python.exe scripts/browser_check.py --url http://127.0.0.1:8512 --output finding_native_browser_results.json --artifact-dir local_data/finding_native_browser
.venv/Scripts/python.exe scripts/verify_finding_geometry.py
```

Run browser journeys sequentially: the application intentionally permits only
one active analysis. An exploratory simultaneous native/new browser run produced
a timing failure while awaiting asynchronous upload invalidation; the final
new workflow waits for upload completion and report invalidation, with the same
assertions, and runs after the native journey. Early browser checks also detected
an ancestor/child expander selector collision and Streamlit's default lossy image
encoding. Selectors now identify the exact expander summary; evidence images
explicitly use PNG and their decoded pixels are independently checked.
Visual review also caught screenshots taken during the mobile sidebar's closing
animation. The final journey waits until the sidebar is outside the viewport,
then captures the unobscured report and verifies that displayed observations,
references, reasons and remediation text equal the shared explanation fields.

Local artifacts (not redistributed in Git):

- `local_data/finding_browser/summary-desktop.png`, `summary-mobile.png`.
- `local_data/finding_browser/OSAGO_SUM-desktop.png`, `OSAGO_SUM-mobile.png`;
  equivalent `OSAGO_PAYMENT-*` and `OSAGO_DECISION_NOTICE-*` captures.
- `local_data/finding_browser/*-pdf.png`: the exact raster displayed by Chromium.
- `local_data/finding_browser/gross_cyrillic-desktop.png`,
  `gross_cyrillic-mobile.png`, `gross_latin-*`, `inson_russian-*`.
- `local_data/finding_browser/reviewed.html`, `reviewed-print.pdf`,
  `print-first-page.png`; originals and malicious-looking annotation text retained.
- `local_data/finding_geometry/`: nine multilingual rule-page images,
  `multiline-rotation-{0,90,180,270}.png`, and the original GROSS Cyrillic page-5
  highlight. `geometry-results.json` contains per-example localization states.
- Existing multilingual journey captures were freshly generated under
  `local_data/i18n_browser/`; the native audit uses `local_data/finding_native_browser/`.

Manual visual inspection checked the synthetic repeated-number page (only the
contractual amount is highlighted), payment/notification day units, Uzbek Latin
and Cyrillic amounts, two distinct lines of a monetary expression, a 90-degree
rotated page, and the original GROSS Cyrillic amount. The latter highlights
**80 000 000 plus its parenthesized amount wording and currency**, leaving the
nearby 28/52-million sublimits unmarked. These image checks supplement offsets
and automated word/character geometry assertions; offset equality alone is not
claimed as visual proof.

## Verified examples and public limitations

| Example | Finding | Location/meaning |
| --- | --- | --- |
| Newly authored total | POTENTIAL_CONFLICT | 60,000,000 UZS on page 2 versus selected 80,000,000 UZS reference; repeated unrelated premium number stays unmarked. |
| Newly authored payment | POTENTIAL_CONFLICT | 9 working days on page 3 versus 5; insurer-decision trigger retained. |
| Newly authored notification | POTENTIAL_CONFLICT | 20 days on page 4 versus 15; written-request trigger and policyholder recipient retained. |
| Unknown date | UNVERIFIABLE | Original quotation/page available; no selected numeric legal version or guessed PDF highlight. |
| Court decision trigger | UNVERIFIABLE | Insurer-decision applicability not established; no contract change recommended. |
| GROSS Latin | 3 UNVERIFIABLE | Damaged text/references retained. Page/quote fallback; no OCR or numeric repair. |
| GROSS Cyrillic | POTENTIAL_CONFLICT, 2 UNVERIFIABLE | Exact page-5 total can be highlighted. Selected 2024 scenario uses the historical reference; old header/newer amount still needs date and legal verification. |
| INSON Russian | 3 UNVERIFIABLE | Damaged amount/sublimit context and statutory appendix evidence remain abstentions; page 23 is not promoted to an offer commitment. |

**Eight of nine public findings remain unverifiable.** These public scenarios are
engineering observations, not expert legal ground truth or proven violations.
Improved localization never changes the engine's status.

## Files changed and remaining scope

Application: `app.py`, `polisdiff/extraction.py`, `polisdiff/extract_worker.py`,
`polisdiff/localization.py`, `polisdiff/presentation.py`, `polisdiff/export.py`,
`polisdiff/i18n.py`, `polisdiff/finding_copy.py`.

Verification: `tests/test_finding_workflow.py`, `scripts/browser_finding_check.py`,
`scripts/verify_finding_geometry.py`, `scripts/browser_check.py`,
`scripts/browser_i18n_check.py`, this result record, the new finding test/count
files and three new finding browser-result files. Documentation:
`docs/FINDING_EXPLANATIONS.md`.

No schema/model change was necessary. The existing engine, catalogue, isolated
analysis service and session invalidation logic were retained. Old JSON remains
readable; source/reviewer content remains escaped. Optional amendment drafts are
omitted because existing reports do not independently establish documentary date
support and sufficient legal/contract context. Rule-specific checklists remain.

Unsupported/unverified: OCR/scans, damaged encodings, arbitrary normalization
repairs, vertical/oblique text, ambiguous geometry/reading order, complex event
paraphrases, independently proven contract dates and historic transition
interpretation. Mapping abstains rather than drawing coarse highlights. Windows
has no verified hard memory cap. No Docker/Dev Container rebuild, public hosting,
complete accessibility audit, real first-time-user study or qualified legal
approval is claimed. No unresolved automated regression is recorded in the final
505-test run; remaining assurance limits are not removed by that result.
