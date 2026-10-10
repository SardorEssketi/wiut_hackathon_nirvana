# Deployment preparation — local only

The user deferred all external hosting. No provider, account, token, billing or
external service is configured. Public deployment remains required later;
local success does not constitute submission readiness.

## Container build and local operation

```powershell
docker build -t polisdiff-ai:local .
docker compose -p polisdiff-local up -d
```

Open `http://localhost:8502`. `main.py` binds `0.0.0.0` and uses the `PORT`
environment variable. Docker build installs the matching CPU PyTorch wheel,
pinned runtime dependencies and revision-pinned E5 weights. Inference disables
downloads. The model is cached in server RAM throughout process/container life.
Image build requires internet; vetted images can then run without egress.

Compose applies local-only port exposure, read-only root, a bounded temporary
filesystem, non-root UID 10001, dropped capabilities, no new privileges, 2 CPUs,
3 GiB memory and 128 PIDs. These are capacity/control settings, not measured
concurrency promises. CPU/model initialization and real PDF analysis must be
measured on the eventual hosting hardware.

OCR is not installed/enabled: no quality-approved OCR path exists. The container
must preserve the text-PDF limit and abstention behavior. Enabling OCR later
requires `uzb`, `uzb_cyrl`, `rus` resources, independent transcription labels,
position tracing and measured quality; installing a binary alone is insufficient.

## Future release checklist

1. Obtain explicit authorization for a new isolated hosting target; use no existing
   unrelated service. Resolve original-code/component release licensing.
2. Select resources from actual RSS/cold-start/real-PDF measurements with headroom;
   do not assume a constrained free instance can support full semantic inference.
3. Build from a recorded commit, pin the Python base digest/dependencies/model,
   record image digest and maintain the pending legal-review status.
4. Configure TLS, authentication, network/upload/connection/rate limits, non-content
   logging and documented retention in an isolated environment.
5. Test the actual public URL in an independent browser, including a previously
   unseen supported PDF, all three languages, source/page evidence and exports.
6. Record URL, provider/resource limits, commit/image/model/catalogue hashes,
   test output and operator authorization. Verify submitted repository matches.

No hosting credentials or paid infrastructure are requested by these instructions.
The current deployment record is explicitly local in `docs/LOCAL_VERIFICATION.md`.
