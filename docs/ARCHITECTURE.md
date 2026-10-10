# Architecture

```mermaid
flowchart LR
    U[Local Streamlit upload + dates] --> V[10 MiB header validation]
    V --> P[Isolated PDF parser / 25 s timeout]
    P --> T[Original page text + offsets + bounding boxes]
    T --> L[Passage script cues + separate normalization]
    L --> S[Offer / appendix segmentation]
    S --> R[Local E5 + BM25 search]
    C[Versioned primary-source catalogue] --> D[Deterministic extraction and comparison]
    R --> D
    D --> E[Four statuses + original evidence]
    E --> H[Session review record]
    H --> X[JSON / escaped HTML export]
    P --> A[Unreadable page: warn + abstain]
```

`polisdiff/models.py`: validated Pydantic data contracts. A report includes document
SHA256, catalogue hash/version, applicability/audit dates, retrieval mode actually
used, model revision, timings, findings and timestamped review actions.

`extraction.py` / `extract_worker.py`: page-level original Unicode text, immutable
page-relative character offsets and positional bounding unions. Sentence and
numbered-clause segmentation crosses layout blocks while preserving exact text.
Oversize, encrypted, malformed and excessive-page/passage inputs are rejected.
Raster previews run in a bounded worker and execute no embedded scripts.

`text.py`: independent NFKC/case/whitespace/apostrophe normalization for search.
No transliteration overwrites evidence. Script and domain-vocabulary cues operate
per passage and allow multiple language labels or an undetermined label.
Thousands separators and decimal conventions are parsed deterministically.

`retrieval.py`: multilingual-e5-small on CPU with query/passage prefixes and a
512-token model limit. Queries are authored in all three language variants.
BM25 uses six-character term prefixes, not a learned model. Hybrid mode uses
reciprocal-rank fusion. Offer and appendix each receive a bounded top-8 search
per rule so copied statutes cannot crowd the offer out. A deterministic topic
scan additionally admits scoped offer passages, preventing ranking from hiding
competing or lower-ranked numeric clauses. It does not validate those clauses;
the engine still checks event, date, currency, ambiguity and section.
The model is cached; each analysis receives fresh mutable passage/query state.
Query vectors are cached per retriever and contain only catalogue queries, not
uploaded text. Passage vectors are cleared after analysis.

`engine.py`: scope/event/unit-aware extraction with a deliberately limited
vocabulary. Select a source version using a user-confirmed applicable date;
unknown, future, unsupported or contradictory dates abstain. The audit date is
not a substitute. Examples/conditions, ambiguous units and competing terms abstain.
References and statutory appendices remain evidence of their own context.

`service.py`: one process-wide active analysis with immediate busy feedback;
real extraction/retrieval/evaluation timings. `runtime.py` shares one cached model
between semantic and hybrid web search modes, with serialized initialization;
each analysis gets a separate retriever. `app.py` does not cache mutable
retrievers. Document state and analyst actions stay per session.
Report exports contain original exact quotations, pages and source-version metadata.

`presentation.py` supplies deterministic Russian summaries, status labels,
observations, reference values and next steps to both Streamlit and HTML.
`session.py` fingerprints PDF bytes, both dates and requested mode; a change
invalidates findings, reviews and previews. Upload/configuration widgets gain
fresh identities after clearing, and review forms are keyed to the report's
document hash and creation time. No browser state can resurrect a prior review
form on a new report. Report schema 1.0 has additive optional provenance fields;
historical JSON remains readable.

No generative LLM supplies legal interpretations or compliance decisions. Network
access is used only to provision dependencies/model and separately research
public sources. The provisioned processing path is fully local. OCR is deliberately
disabled until binary/language resources and independent quality checks exist.

Production extension: authenticated reviewer identity, append-only durable audit
store with retention policy, expert-approved rule versions, process/container
resource isolation, reverse-proxy authentication/rate limiting, more independent
multilingual annotations and monitored date-version maintenance.
