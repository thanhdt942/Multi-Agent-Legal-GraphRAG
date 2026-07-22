from enum import StrEnum
from typing import Any, Literal

from pydantic import Field

from .models import RelationStatus, SearchFilters, StrictModel


class ConversationMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class AnswerRetrievalOptions(StrictModel):
    strategy: Literal["semantic", "hybrid", "graph", "auto"] = "auto"
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=12, ge=1, le=50)
    relationship_statuses: list[RelationStatus] = Field(
        default_factory=lambda: [RelationStatus.VERIFIED]
    )
    context_token_budget: int = Field(default=12_000, ge=1, le=24_000)


class GenerationOptions(StrictModel):
    language: Literal["vi"] = "vi"
    format: Literal["markdown", "text"] = "markdown"
    temperature: float = Field(default=0.1, ge=0, le=1)
    max_output_tokens: int = Field(default=800, ge=128, le=4000)
    require_citations: bool = True
    abstain_when_insufficient: bool = True


class AnswerRequest(StrictModel):
    question: str = Field(min_length=3, max_length=4000)
    messages: list[ConversationMessage] = Field(default_factory=list, max_length=20)
    retrieval: AnswerRetrievalOptions = Field(default_factory=AnswerRetrievalOptions)
    generation: GenerationOptions = Field(default_factory=GenerationOptions)
    include_retrieval: bool = False
    thread_id: str | None = Field(default=None, min_length=1, max_length=128, pattern=r"^[\w.-]+$")


class SituationAnalysis(StrictModel):
    summary: str
    facts: list[str]
    legal_issues: list[str]
    applicable_date: str | None
    legal_references: list[str]
    retrieval_queries: list[str] = Field(min_length=1, max_length=3)
    requires_historical_comparison: bool
    missing_facts: list[str]
    should_abstain: bool


class ClaimSupport(StrEnum):
    DIRECT = "DIRECT"
    INFERRED = "INFERRED"
    UNSUPPORTED = "UNSUPPORTED"


class AnswerConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class LegalClaim(StrictModel):
    text: str
    citation_ids: list[str]
    support: ClaimSupport


class DraftAnswer(StrictModel):
    answer: str
    claims: list[LegalClaim]
    confidence: AnswerConfidence
    abstained: bool


class CriticDecision(StrEnum):
    PASS = "PASS"
    RETRIEVE_MORE = "RETRIEVE_MORE"
    COMPARE_MORE = "COMPARE_MORE"
    ABSTAIN = "ABSTAIN"


class CritiqueResult(StrictModel):
    decision: CriticDecision
    findings: list[str]
    missing_evidence_queries: list[str] = Field(default_factory=list, max_length=3)


class ModelUsage(StrictModel):
    input_tokens: int = 0
    output_tokens: int = 0


class Citation(StrictModel):
    citation_id: str
    node_id: str
    document_id: str | None = None
    document_number: str | None = None
    document_name: str | None = None
    chapter: str | None = None
    section: str | None = None
    article: str | None = None
    clause: str | None = None
    point: str | None = None
    display: str = ""
    quote: str = ""
    source_url: str | None = None
    validity_status: str | None = None
    retrieved_at: str | None = None


class AnswerResponse(StrictModel):
    answer_id: str
    thread_id: str
    retrieval_id: str | None
    answer: str
    citations: list[Citation]
    claims: list[LegalClaim]
    confidence: AnswerConfidence
    abstained: bool
    warnings: list[str]
    usage: ModelUsage
    retrieval: dict[str, Any] | None = None
