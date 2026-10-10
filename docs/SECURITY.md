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
  Fresh mutable retrievers are allocated for each analysis; uploaded passages
  and vectors are cleared afterwards. Initialization of the shared model is
  serialized. Query dictionaries are separate and contain only catalogue text.
- Uploaded document contents and identifiers are not emitted by application
  logging. Worker tracebacks/PDF diagnostics are not forwarded to app logs.
  Research scripts intentionally inspect public samples and are not production
  document-processing endpoints.
- HTML report escapes all extracted text and reviewer rationale. UI evidence uses
  plain-text code blocks. Custom HTML styling contains only static project markup.
  Report source links allow only HTTPS LexUZ URLs on the standard port;
  javascript/data URLs and malformed links never become active anchors. An inline
  content-security policy blocks scripts, network content and form submission in
  the self-contained export. Print layout needs no external fonts or CDN.
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
Report/widget identities also prevent a browser-preserved rationale from being
reused on another analysis. Configuration changes remove the prior report,
reviews and evidence preview; “Clear session” assigns new configuration/upload
widget keys so client state resets as well.

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

This audit did not establish enterprise security, a Windows memory ceiling,
secure RAM erasure, legal approval or licence compliance. The supported file
limits and timeouts do not eliminate every native-parser/decompression risk.
No confidential samples were used for browser verification. No new external AI
service or hosting provider was introduced.
