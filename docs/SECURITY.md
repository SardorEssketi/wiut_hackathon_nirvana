# Security and retention

The current local demo accepts public, original synthetic or properly anonymized
PDFs. It is not an approved environment for confidential customer documents.

## Implemented controls

- Strict PDF header, 10 MiB file limit, 80-page / 500,000-character / 1,800-passage
  resource limits. Encrypted or unparseable PDFs are rejected without made-up text.
- Parsing runs in a separate process with a 25-second wall timeout. Linux adds
  768 MiB address-space and 20-second CPU limits; Windows has the wall timeout.
- Rendering has a separate 15-second timeout and scales the longest edge to at
  most 1,400 pixels. Original links, scripts and embedded files are not executed.
- One active analysis per server process and a five-second session cooldown.
  This is basic abuse protection, not a public multi-tenant rate-limit system.
- Runtime local model files only, Hugging Face offline flags, no external LLM API.
  The two web AI search modes share one cached embedding model per process.
  Uploaded passages/vectors are cleared
  from the shared retriever after each analysis.
- Uploaded document contents and identifiers are not emitted by application
  logging. Worker tracebacks/PDF diagnostics are not forwarded to app logs.
  Research scripts intentionally inspect public samples and are not production
  document-processing endpoints.
- HTML report escapes all extracted text and reviewer rationale. UI evidence uses
  plain-text code blocks. Custom HTML styling contains only static project markup.
- Streamlit CORS/XSRF protection and disabled browser usage statistics.
- Docker non-root user, Compose read-only root, dropped capabilities, no new
  privileges, CPU/memory/PID limits, loopback-only published port.

## Retention

Application upload bytes, extraction and reports remain in server RAM for the
browser session. No upload/report disk persistence is implemented. “Clear session”
removes active session state; framework disconnected-session TTL is configured
as 60 seconds. This is not guaranteed secure memory wiping or a verified privacy
deletion SLA. Runtime crash dumps/swap are OS responsibilities. Explicit exports
remain on the analyst's device until the analyst deletes them. Review actions are
lost when the session is cleared; export before leaving.

Research inputs, browser test downloads and screenshots live in ignored
`local_data/`, separate from actual user uploads. Original third-party PDFs never
enter Git or Docker. Only original synthetic reports are checked in as evaluation
artifacts. No hardcoded credentials or hosting-service configuration.

## Before any public/organizational deployment

Use an isolated host with an authenticated reverse proxy, TLS, connection/request
limits and operator-controlled access logs that exclude document text/identifiers.
Confirm memory/cold-start headroom with representative unseen inputs and keep
confidential inputs out of an unapproved public environment. Obtain qualified
legal review and resolve component/application licensing. Public deployment is
currently deferred and has not been verified.
