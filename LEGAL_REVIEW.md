# Legal review state

All three engineering interpretations: **PENDING_LEGAL_REVIEW**.
No qualified legal reviewer has approved the catalogue. The user expressly
requested that this status remain visible. `PRIMARY_TEXT_VERIFIED` means the
engineering assistant inspected the accessible primary text; it does not imply
human review, legal certification or partner approval.

## Narrow checks

| Check | Verified provision | Engineering operation | Unresolved legal interpretation |
| --- | --- | --- | --- |
| Total insurance sum | Resolution 141, operative paragraph 1, second subparagraph; historical/current versions | Compare one explicit total in UZS with the version for a user-confirmed contract date | Existing-contract transition treatment; mixed/header dates; partial limits; examples |
| Indemnity payment deadline | Appendix 4 paragraph 66 | Compare explicit working-day payment deadline from the insurer's adopted payment decision | More favorable terms, exceptions, calendar-day wording, documents with another payment trigger |
| Decision notification deadline | Appendix 4 paragraph 67, current annotation for 2024 amendment | Compare notification to policyholder after written/electronic indemnity request | Interpretation of unqualified days; electronic/written trigger, recipient, taking a decision versus notifying it |

The source text addresses substantive insurance obligations. This prototype has
**not established a general duty to reproduce them verbatim in every public
offer**. It does not audit compensation-fund obligations, premium tariffs,
property/life sublimits, penalties, every insurer obligation or state-language
disclosure law. Language detection is a technical observation only.

## Outcomes and abstention

`MATCH_FOUND`: an explicit term matches the limited engineering check.
`POTENTIAL_CONFLICT`: an explicit comparable term differs from the version's
numeric target; an analyst must assess context and law.
`NOT_FOUND`: supported text was not found among retrieved passages. Search can
miss evidence; this is not proof of a legal violation.
`UNVERIFIABLE`: unknown/out-of-range date, damaged text, competing values,
unsupported units, conditional wording, reference incorporation or appendix-only
evidence prevents the comparison.

Contract applicability date and audit date are distinct. First-page dates are
shown as hints and are never automatically treated as applicable dates.
Without user confirmation, all checks abstain. Dates before 5 August 2024 or
after 10 October 2026 are unsupported. Existing contracts crossing the 2026
change need legal review; a user selecting a date is not proof of transition
applicability. Historical files are not silently judged by today's version.

## Incorporation and document authorship

A detected reference to rules approved by Resolution 141 is documentary evidence
of a reference, not proof of valid or complete incorporation. Where no explicit
term is found, reference evidence produces `UNVERIFIABLE`. Statutory appendices
are searched separately and labelled; a match there does not establish the
author's offer contains the same contractual obligation. Section detection is a
heading/attribution heuristic and must be reviewed.

## Review record

The local demo analyst can confirm, dismiss or request further review, with
UTC timestamp and rationale. Actions are append-only within a session and exported
with the original algorithm finding. They do not upgrade `PENDING_LEGAL_REVIEW`,
authenticate a professional reviewer or persist as a regulatory audit database.

Before production: a qualified reviewer must approve rule scope, effective-date
and transition assumptions, supported wording and abstention policy. Approval
needs a new reviewed catalogue version; the prototype cannot manufacture it.
