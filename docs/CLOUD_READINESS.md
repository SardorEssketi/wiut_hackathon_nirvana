# Cloud readiness and date workflow

The numerical engine, catalogue and exact PDF localization remain unchanged.
Readiness and compact findings are deterministic presentation of existing
statuses. Unknown applicability dates still yield three `UNVERIFIABLE` findings,
without regulatory numerical references or source quotes for an unselected date.
The UI shows the shared blocker once, keeps pending checks compact, and links to
the date controls. The user must enter a date and explicitly confirm it against
the original agreement; the upload date, filename and detected PDF header dates
are never substituted. Changing inputs invalidates the report, annotations and
selected preview. Details, legal sources and conditional guidance remain available
on demand; HTML uses the same explanations, collapses pending details on screen
and exposes the original evidence for A4 printing. JSON schema 1.0 is unchanged.

## Why local AI and Cloud differ

`models/` is ignored by Git. The validated local machine contains E5 files; the
default path on Cloud is the checkout's `models/multilingual-e5-small/`, not the
local Windows path. A tracked `model_manifest.json` is provenance, not weights.
The normal Cloud entry point installs `requirements.txt` and runs `app.py`; it
does not run the Dockerfile's provisioning step or `main.py`. Runtime forces
`HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, and `SentenceTransformer` uses a
local path, `local_files_only=True`, CPU and no remote code. Missing files produce
an explicit lexical fallback without importing/loading the AI stack.

Before the change, actual public Cloud browser reports requested `hybrid` but
used `lexical`, with `FileNotFoundError` and no model revision. That establishes
missing provisioning; it does not establish an out-of-memory failure. Private
owner logs were not supplied. Startup retains one shared model and makes session
copies of document/query state; failed loads are cached until process restart.

The core local model files total **487,725,572 bytes** (weights 470,641,600 bytes).
Prior Linux CPU measurements in `evaluation/container_results.json` and
`docs/LOCAL_VERIFICATION.md` measured a 13.341 s initialization and 1191.3 MiB
main-process peak; a separate full service run peaked at 1032.1 MiB. These are
different historical runs, not measurements of this Cloud host. The
[Cloud documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
publishes approximate resource ranges dated February 2024 and says they can
change. Read the actual deployed cgroup budget instead of assuming the maximum.

## Controlled provisioning without paid infrastructure

The default remains offline and performs no download. An app owner can explicitly
enable a single provisioning attempt per process by setting this root-level
[Cloud secret](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management):

```toml
POLISDIFF_PROVISION_MODEL = "1"
POLISDIFF_TORCH_THREADS = "2"
```

Before downloading, the process must measure a cgroup memory limit of at least
2 GiB and available headroom of at least 1536 MiB. Unknown or smaller budgets
abstain. This margin is an engineering gate, not a guarantee under concurrent
load. The owner-enabled readiness notice explains the preparation before users
start analysis. The existing downloader runs in a separate process, with a
180-second timeout, the pinned E5 revision
`614241f622f53c4eeff9890bdc4f31cfecc418b3`, and only the CPU inference files.
`POLISDIFF_MODEL_PATH` is honored; its directory must be writable when provisioning
and readable afterward. No uploaded document bytes are sent to the downloader.
Its Hugging Face online flag applies only in the child; parent inference remains
offline. Download failures are cached, not retried on every session. Existing
files are reused. A fresh ephemeral host/restart may need preparation again.

The dependency file pins the verified Streamlit 1.65.0 and CPU Torch 2.14.1+cpu
to avoid version drift and unnecessary CUDA packages. The official CPU wheel
index was checked for Linux CPython 3.14/x86-64 availability. The local verified
pipeline uses Python 3.12.6; this index check alone is not a Cloud installation or
AI success claim. The Docker path retains the tested Linux/Python 3.12 CPU stack.

Do not infer successful AI use from files present or an installed package. Check
an actual report's `retrieval_used` and `model_revision`. If loading, downloading,
resources or host support fail, lexical mode remains clearly marked **without AI**.
No external AI API, quantized replacement model, paid server or changed reference
value is introduced. An owner may alternatively provision the same trusted files
at build time (the existing Docker path) or via an explicitly maintained Git LFS
artifact; large model files are not committed by this change.

## Deployment identity and diagnostics

The technical expander offers a JSON download containing the actual Git HEAD,
a source-content SHA-256, Python and installed package versions, configured model
path/file presence, offline flags, cgroup CPU/memory values and provisioning state.
No uploads, quotations, annotations, credentials or unrelated environment values
are included. HEAD alone can differ from a dirty/mixed checkout; compare both HEAD
and source-content hash. An absent Git directory is reported as unknown rather
than invented. Presence of files is labelled separately from successful AI use.

After source or secrets changes, reboot the Cloud process when required. Python
can retain previous modules despite reloading the entry point; startup checks the
new APIs and asks for a reboot rather than reloading modules used by other sessions.
Export annotations before a planned restart: in-memory sessions are lost. A
requirements change triggers dependency installation on Cloud; monitor owner
build logs and then verify the revision in the diagnostics download.

## Validation record

Fresh baseline: **509 passed in 53.39s**. The first full changed suite passed
**536 in 44.24s** before adding the two headroom regression cases. Further exact
results, source/deployment SHAs and browser outcomes are recorded in
`evaluation/CLOUD_RESULTS.md`. Existing tests were not removed or weakened.
The new browser script accepts the public Cloud iframe and localhost, verifies
unknown/supported dates, a real GROSS Latin PDF, three synthetic conflicts,
actual AI/fallback fields, precise raster equality, desktop/mobile, A4 pending
evidence, escaped HTML/JSON, reviews, isolation and input invalidation.
