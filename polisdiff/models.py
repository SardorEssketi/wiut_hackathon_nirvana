from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field


class Status(StrEnum):
    MATCH_FOUND = "MATCH_FOUND"
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    NOT_FOUND = "NOT_FOUND"
    UNVERIFIABLE = "UNVERIFIABLE"


class Passage(BaseModel):
    id: str
    page: int
    text: str
    normalized: str
    start: int
    end: int
    bbox: tuple[float, float, float, float]
    languages: list[str]
    section: Literal["offer", "regulatory_appendix", "uncertain"] = "offer"


class Page(BaseModel):
    number: int
    text: str
    chars: int
    readable: bool
    extraction: str = "text"
    section: str = "offer"


class Document(BaseModel):
    sha256: str
    pages: list[Page]
    passages: list[Passage]
    languages: list[str]
    warnings: list[str]
    detected_dates: list[date] = Field(default_factory=list)
    governing_reference: list[Passage] = Field(default_factory=list)


class RuleVersion(BaseModel):
    effective_from: date
    effective_to: date | None
    expected: float
    source_url: str
    source_quote: str
    version_note: str


class Rule(BaseModel):
    id: str
    name: str
    product: str
    applicability: str
    reference: str
    official_source: str
    legal_text_status: str
    reviewer_status: Literal["PENDING_LEGAL_REVIEW"]
    interpretation: str
    extraction_requirements: list[str]
    uncertainty_conditions: list[str]
    logic: Literal["sum", "payment_days", "decision_days"]
    queries: list[str]
    versions: list[RuleVersion]


class Evidence(BaseModel):
    passage_id: str
    page: int
    quote: str
    start: int
    end: int
    bbox: tuple[float, float, float, float]
    section: str
    extracted_value: float | None = None
    unit: str | None = None


class Finding(BaseModel):
    rule_id: str
    rule_name: str
    status: Status
    reason: str
    evidence: list[Evidence]
    source_url: str
    provision_reference: str
    source_quote: str
    effective_from: date | None
    effective_to: date | None
    expected_value: float | None
    reviewer_status: str = "PENDING_LEGAL_REVIEW"
    manual_review_required: bool = True
    uncertainty: list[str] = Field(default_factory=list)
    check_scope: str = ""
    source_version_note: str = ""


class ReviewAction(BaseModel):
    rule_id: str
    action: Literal["confirm", "dismiss", "further_review"]
    rationale: str = Field(min_length=3, max_length=2000)
    timestamp: datetime
    actor: str = "local_demo_analyst"


class Report(BaseModel):
    schema_version: str = "1.0"
    application_version: str = "0.2.0"
    rules_catalogue_version: str
    rules_catalogue_sha256: str
    document_sha256: str
    audit_date: date
    applicable_date: date | None
    date_basis: str
    product: str = "OSAGO (user selected)"
    created_at: datetime
    detected_languages: list[str]
    page_count: int
    warnings: list[str]
    retrieval_requested: str
    retrieval_used: str
    model_revision: str | None = None
    candidate_selection: str = "top_8_per_section"
    timings_seconds: dict[str, float]
    findings: list[Finding]
    reviews: list[ReviewAction] = Field(default_factory=list)
    disclaimer: str = (
        "Evidence screening of three provisions only; no binding legal determination or "
        "whole-document compliance claim. NOT_FOUND is not proof of a violation. "
        "All engineering interpretations are PENDING_LEGAL_REVIEW."
    )
