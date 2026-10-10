# PolisDiff AI

Offline multilingual evidence screening for public Uzbek OSAGO insurance offers.
Python + Streamlit + PyMuPDF + locally provisioned multilingual E5 + deterministic,
date-versioned rules. Initial interface: Russian. Document variants: Uzbek Latin,
Uzbek Cyrillic, Russian, and mixed passages.

**Local prototype; not submission-ready.** Public deployment is deferred by the
user and must later pass an independent browser test. All engineering legal
interpretations are **PENDING_LEGAL_REVIEW**. Three checks cannot certify an
entire document. `NOT_FOUND` does not mean a violation.

## Quick start — Windows PowerShell

Run from this repository. Python 3.12 was used in the actual local run.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock.txt
.venv/Scripts/python.exe scripts/download_model.py
.venv/Scripts/python.exe main.py
```

Open [localhost:8501](http://localhost:8501). The model provisioning step downloads
weights once; subsequent analysis runs offline. Pin model provisioning to the
recorded revision if creating a fresh environment:

```powershell
$env:POLISDIFF_MODEL_REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'
.venv/Scripts/python.exe scripts/download_model.py
```

The existing workspace `.venv` and `models/` are ready after this session's setup.
The app honors `PORT` (default 8501) and binds `0.0.0.0`; firewall exposure is an
operator decision. `.env.example` is a reference; no dotenv autoloading or
credentials are needed. Runtime explicitly disables Hugging Face downloads.
Automatic source watching is disabled to avoid Transformers lazy-import watcher
errors; restart the server after changing application code or configuration.

## Linux / financial organization's offline perimeter

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1
.venv/bin/python -m pip install -r requirements.runtime.lock.txt
POLISDIFF_MODEL_REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3 .venv/bin/python scripts/download_model.py
.venv/bin/python main.py
```

Provision packages/weights on an authorized build machine, then transfer the
image or vetted dependencies and model files into the perimeter. Inference sends
no uploaded PDF/text to external AI APIs. The local model is cached for the server
process lifetime. Model/download metadata is in `evaluation/model_manifest.json`.

## Use

1. Upload an authorized OSAGO PDF, up to 10 MiB and 80 pages.
2. Choose the audit date and explicitly confirm the contract applicability date.
   Unknown dates produce abstention. Historical headers are hints, not authority.
3. Run hybrid AI + lexical retrieval, semantic retrieval, or the lexical baseline.
   Missing model weights cause an explicit labelled lexical fallback.
4. Review the four statuses, original Unicode quotations, actual pages,
   provision references, legal-version dates and warnings.
5. View the rasterized PDF page and extracted original text. Appendix classification
   is heuristic and always requires manual review.
6. Record confirm/dismiss/further-review with a rationale. Download JSON or HTML.
   Review data lives only in the session; export before clearing it.

Supported dates: 05.08.2024–10.10.2026. Checks: total insurance sum, indemnity
payment after the insurer's decision, decision notification after an indemnity
request. See [legal review](LEGAL_REVIEW.md) and [catalogue](rules/catalogue.v1.json).

**OCR is disabled.** Tesseract was absent and no OCR-quality metrics were produced.
Scans and damaged text result in warnings/abstention. The GROSS Latin public
sample demonstrates the current degraded-text limitation rather than a fake pass.

## Reproduce tests and measurements

The checked-in synthetic PDFs are original project fixtures. The generator uses
an installed Unicode font; regeneration on another OS may alter PDF hashes.
Developer dependencies and Chromium are required for browser checks.

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe evaluation/generate_fixtures.py
.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/pytest_temp --junitxml=evaluation/tests.final.xml
.venv/Scripts/python.exe scripts/test_summary.py evaluation/tests.final.xml
.venv/Scripts/python.exe scripts/research_sources.py
.venv/Scripts/python.exe evaluation/benchmark.py
.venv/Scripts/python.exe -m playwright install chromium
.venv/Scripts/python.exe scripts/browser_check.py
.venv/Scripts/python.exe scripts/local_smoke.py
.venv/Scripts/python.exe scripts/integrity_check.py
```

Keep the actual app running in another terminal for `browser_check.py`. The PDF
research script downloads into ignored storage and records availability honestly.
Full suite includes actual offline embeddings, malformed/encrypted/oversized PDFs,
scanned-page abstention, dates, Unicode, original evidence and fresh synthetic text.
`--basetemp` is inside this project to avoid the observed Windows temp ACL failure.
Pytest resets that dedicated temporary directory on subsequent runs.

Results: [evaluation report](evaluation/RESULTS.md),
[raw benchmark](evaluation/benchmark_results.json),
[local browser record](evaluation/browser_results.json).
Small synthetic labels are not expert legal validation; the original evaluation
split was exposed while debugging and is identified as regression evaluation.
Fresh wording is reported separately. There is no independently verified public URL.

## Docker

```powershell
docker build -t polisdiff-ai:local .
docker compose -p polisdiff-local up -d
```

An explicit offline container analysis check (after downloading the public inputs):

```powershell
.venv/Scripts/python.exe scripts/run_container_check.py
.venv/Scripts/python.exe scripts/browser_check.py --url http://localhost:8502 --output browser.container_results.json
```

The isolated Compose service binds localhost port 8502 and uses a non-root user,
read-only root filesystem, dropped capabilities, and bounded memory/processes.
The Docker build provisions the pinned model; runtime disables downloads.
Review [deployment preparation](docs/DEPLOYMENT.md) and
[actual local verification](docs/LOCAL_VERIFICATION.md) for build/test evidence.
Future hosting must accommodate measured memory, startup and CPU latency.
Native and Docker browser results include actual historical and unknown-date checks;
the local verification record identifies the tested image and matching source commit.

## Documentation and release constraints

- [Primary sources](SOURCES.md), [data and software licenses](DATA_LICENSES.md).
- [Architecture](docs/ARCHITECTURE.md), [security and retention](docs/SECURITY.md).
- [Known limitations](docs/LIMITATIONS.md), [business assumptions](docs/BUSINESS_CASE.md).
- [Seven-minute defense](docs/DEFENCE.md), [development provenance](docs/DEVELOPMENT_HISTORY.md).

No official partnership, legal certification or measured customer savings.
No reused application from another project. Codex-generated code, fixtures and
evaluation annotations are disclosed; model/library authorship belongs to their
respective projects. Resolve PyMuPDF/whole-application release licensing before
public distribution or a closed commercial deployment.
