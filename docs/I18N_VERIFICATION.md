# Interface and report languages

Russian remains the initial interface. The sidebar now also offers Uzbek Latin
(`uz-Latn`, O‘zbekcha), Uzbek Cyrillic (`uz-Cyrl`, Ўзбекча (кирилл)) and English
(`en`). Interface labels, date explanations, progress stages, status summaries,
rule titles/scopes, extracted values/units, known deterministic reasons, next
steps, analyst actions and self-contained printable HTML follow this preference.

`polisdiff/i18n.py` is the central catalogue of 223 interface phrases/templates.
The presentation and
export functions accept an optional language argument with `ru` as their default,
so existing callers retain Russian. No translation service, API or dependency was
introduced. The document-processing and rule engine are unchanged. English UI
support does not imply English-document extraction/rule coverage.

Original PDF quotations, legal quotations, official source references, version
notes and analyst-entered rationale are preserved exactly. Catalogue interpretation
text is explicitly labelled as original wording. JSON retains its existing fields
and original reasons/statuses; changing presentation language does not mutate a
report. Known warnings/uncertainty reasons are localized. Unknown/custom recorded
reasons remain explicitly identified as original text.

## State correctness discovered in the real browser

File: `polisdiff/session.py`, `preserve_translated_choices` /
`restore_translated_choices`; the sidebar language selector in `app.py`.

Observed defect during implementation: Streamlit 1.65 serializes radio/selectbox
choices using their formatted display text. After translating those options, an
old displayed search choice was no longer recognized, reset to hybrid, and
invalidated a lexical report. Stable underlying option IDs alone were insufficient.

Fix: the language-change callback snapshots only search/reviewer option IDs using
the previous widget deserializers, and restores them before rendering translated
widgets. Document bytes/reports are not copied. This also preserves the selected
review rule/action. The existing document/date/mode fingerprint remains unchanged;
language is a presentation preference. Clearing removes results, reviews and
configuration while retaining the language. Preferences remain session-local.

## Reproduction

```powershell
.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/i18n_delivered_tmp --junitxml=evaluation/i18n_tests.xml
.venv/Scripts/python.exe scripts/test_summary.py evaluation/i18n_tests.xml
.venv/Scripts/python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501
# Run against the live local app from a second terminal:
.venv/Scripts/python.exe scripts/browser_i18n_check.py
.venv/Scripts/python.exe scripts/browser_check.py --output i18n_russian_browser_results.json
```

Fresh pre-change baseline: **175 passed**, 69.17 seconds. Completed full suite:
**459 passed, zero failures/errors/skips**, 42.44 seconds. Single-run timings are
machine/load dependent, not performance improvements. Results:
[counts](../evaluation/i18n_tests.json), [JUnit](../evaluation/i18n_tests.xml).
New coverage checks all 64 combinations of three findings across four statuses in
each interface language, translation/placeholder completeness, all static engine
reasons, missing evidence/dates, source and review preservation, escaping, custom
reason fallback, unsupported language rejection and option-ID snapshots.

The [multilingual Chromium record](../evaluation/i18n_browser_results.json) covers
all nine combinations of three new UI languages and three supported PDF script
variants, with zero horizontal overflow. It also checks desktop/mobile evidence,
unchanged reports/reviews and selected review choices/rationale across language
switches, unknown-date abstention, clear/session isolation and HTML/JSON
exports. Each new language's HTML is opened without external requests and printed
to A4. Screenshots, downloaded reports and printed PDFs remain in ignored
`local_data/i18n_browser/`. The additional Russian compatibility browser record
includes all seven original/public/newly authored inputs and the historical
applicability scenario. Desktop/mobile and all three printed cover pages were
visually inspected. Both final browser records report no page errors or external
resource requests. Driver waits explicitly assert old frontend widget removal,
single tab controls and responsive sidebar expansion before clicking; evidence
assertions target the active findings panel rather than duplicate hidden tab text.

## Limits

Translations are engineering interface copy, not certified legal translations;
native-speaker usability review remains advisable. Browser/Streamlit-owned file
picker, calendar and navigation labels may follow the browser/framework language.
No legal source quotation is translated. All interpretations remain
PENDING_LEGAL_REVIEW, only three OSAGO checks are screened, and OCR is unsupported.
No new benchmark accuracy claim is made: deterministic analysis source files were
not changed. Earlier audit/benchmark records retain their original source hashes.
No hosting or Dev Container execution was performed.
