# Actual local verification

Recorded: 2026-10-10T11:40:29.321750+00:00. Source checkpoint: `ff40517a44be70ad2001effb6d9d83c1b1a8e7f6`.

**Local prototype only; not hackathon submission-ready.** No public hosting
was configured. Public deployment requires later authorization and an independent browser test.

## Commands actually exercised

```powershell
.venv/Scripts/python.exe main.py
.venv/Scripts/python.exe -m pytest -q --basetemp=local_data/pytest_temp --junitxml=evaluation/tests.final.xml
.venv/Scripts/python.exe scripts/browser_check.py
.venv/Scripts/python.exe scripts/local_smoke.py
docker build -t polisdiff-ai:local .
.venv/Scripts/python.exe scripts/run_container_check.py
docker compose -p polisdiff-local up -d --no-build
.venv/Scripts/python.exe scripts/browser_check.py --url http://localhost:8502 --output browser.container_results.json
.venv/Scripts/python.exe scripts/local_smoke.py --url http://localhost:8502 --output smoke.container_results.json
```

Native UI: [localhost:8501](http://localhost:8501). Isolated Compose UI:
[localhost:8502](http://localhost:8502). Servers use `0.0.0.0` internally;
Compose publishes only the host loopback interface. A separate local container
also verified a changed `PORT=8503` through host port 8502 before Compose testing.

## Actual checks

- Complete suite: **67 passed, 0 failed, 0 errors, 0 skipped**.
- Native Chromium: 7 supported PDFs; success `True`.
- Docker Chromium: 7 supported PDFs; success `True`.
- Each full journey includes three script variants, a separately authored unseen
  fixture, three actual public PDFs, exact quote/page checks, JSON/HTML review
  exports, raster preview, mobile content and session clearing.
- Fresh-start smoke checks exercise unknown-date abstention, changing the audit
  date into 2024, the historical 40-million source version, and both AI modes.
- Offline read-only/non-root container: 6 PDFs; UID 10001; networking disabled.
- Container CLI model initialization: 13.341 s; peak main-process RSS 1191.3 MiB.
- Full service cgroup peak: 1032.1 MiB, within configured 3.0 GiB. OOM kills: 0.
- Health: `healthy`. Image: `sha256:6934a0faa6da2ea1aa407dc3cffbff31457b317d209c7bb028745ee623084e0b`.
- All 16 recorded application/configuration source hashes match the tested image and committed source checkpoint.
- Dataset/model/public-input integrity: 56 recorded hashes and Git exclusion checks; success `True`.

The offline CLI memory measurement excludes parser children; the service cgroup
peak includes the container processes. These are different runs. Single-machine
measurements do not establish production throughput, free-tier suitability or an SLA.

## Evaluation and limitations

Fresh synthetic hybrid status accuracy: 88.9% across 9 labels; conflict recall 80.0%.
One Russian payment phrase was retrieved but missed by deterministic extraction.
Real samples abstain extensively; no expert legal ground truth or AI accuracy gain
is established. OCR remains disabled, with scans explicitly unsupported.
All interpretations remain `PENDING_LEGAL_REVIEW`. No finding certifies an entire policy.

Artifacts: [tests](../evaluation/tests.final.json),
[native browser](../evaluation/browser_results.json),
[Docker browser](../evaluation/browser.container_results.json),
[offline container](../evaluation/container_results.json),
[image/source/resource record](../evaluation/local_release_manifest.json),
[benchmark](../evaluation/RESULTS.md), [limitations](LIMITATIONS.md).
