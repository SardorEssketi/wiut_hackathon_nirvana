# Development provenance

The user confirmed in this session that the official final stage had started and
authorized implementation. The exact organizer start timestamp has not been
provided or independently verified. Before that confirmation the assistant
performed only environment inspection and read-only source research.

Initial repository inspection: no commits; an empty `main.py` and IDE metadata.
No application code was reused from another project. Implementation is being
written with an OpenAI Codex coding assistant. Python dependencies, the E5 model,
MuPDF, Streamlit and other libraries are external components; their authorship
and licenses must be disclosed. Synthetic test text and fixture generation code
are original AI-assisted work. No partner endorsement or legal certification.

The user subsequently changed the strategy to local-first development and
revoked deployment authorization for now. No hosting account is configured and
no hosting credentials are requested. Public deployment and independent public
browser verification remain required before hackathon submission readiness.
Legal interpretations are explicitly awaiting human legal review, as directed
by the user. Source verification by an engineering assistant is not human legal
review.

## Actual engineering checkpoints

- `5caf306`: first source-grounded extraction, date-versioned engine, offline
  retrieval and working Streamlit implementation.
- `73aa5a5`: measured evaluation, Docker packaging and local reliability fixes.
- `ff40517`: responsive content verification and preserved full-suite rerun.
- Initial tests exposed multilingual payment recognition, Unicode rule-reference
  normalization and Windows fixture/temp-directory problems. Failure artifacts
  are retained under `evaluation/tests.initial.*`; no failing case was skipped.
- The original evaluation wording was used while debugging, so its metrics are
  identified as regression results. Fresh separately authored wording was then
  evaluated without adjusting the engine from those outcomes. It exposed a
  Russian payment-event recognition miss, retained in the reported results.
- Browser checks exposed rerun/download synchronization issues and a real clear
  session defect. The uploader now gets a new widget identity after clearing;
  removing a file also releases the report/document references.
- Both web AI modes now share one embedding model. Tests verify that shared
  model caching does not share uploaded passage state. Invalid page previews
  are rejected before spawning a parser.
- The complete local suite reached 67 passed, zero failures/errors/skips.
  A real CPU Docker image was built and six public/synthetic PDFs were processed
  under network-disabled, read-only, non-root execution. Browser and image
  identity records are linked from `LOCAL_VERIFICATION.md`.
- Fresh-start web checks validate unknown dates and a historical audit date in
  both AI modes. Runtime source watching is disabled after actual Transformer
  lazy imports produced unnecessary framework watcher errors.
- Evaluation JSON bytes are preserved in Git to keep recorded manifest hashes
  reproducible. Source text uses LF line endings. Test-run environment dumps are
  redacted from failure artifacts; failure counts and underlying errors remain.
- Final local image verification matched 16 application/configuration hashes to
  the committed source checkpoint. Native and final Compose browser journeys
  each passed all seven inputs; both fresh-start date/mode checks passed.
  Public deployment remains deferred; these records do not declare submission
  readiness.

The assistant wrote code, synthetic text, fixtures, engineering labels,
documentation and evaluation scripts with user authorization. Model weights and
Python dependencies are external work, provisioned during implementation. No
external collaborator or qualified legal reviewer has approved this prototype.
