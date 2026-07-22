from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Level(StrEnum):
    DOCUMENT = "document"
    CHAPTER = "chapter"
    SECTION = "section"
    ARTICLE = "article"
    CLAUSE = "clause"
    POINT = "point"


class RelationshipType(StrEnum):
    HAS_CHILD = "HAS_CHILD"
    THAY_THE = "THAY_THE"
    SUA_DOI = "SUA_DOI"
    TUONG_UNG = "TUONG_UNG"
    DAN_CHIEU = "DAN_CHIEU"
    AP_DUNG_CHUYEN_TIEP = "AP_DUNG_CHUYEN_TIEP"
    LAM_HET_HIEU_LUC = "LAM_HET_HIEU_LUC"
    VI_PHAM = "VI_PHAM"


class RelationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PROPOSED = "PROPOSED"


class SearchFilters(StrictModel):
    document_ids: list[str] = Field(default_factory=list, max_length=100)
    document_numbers: list[str] = Field(default_factory=list, max_length=100)
    levels: list[Level] = Field(default_factory=list)
    validity_statuses: list[str] = Field(default_factory=list, max_length=20)
    issued_from: date | None = None
    issued_to: date | None = None

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "SearchFilters":
        if self.issued_from and self.issued_to and self.issued_from > self.issued_to:
            raise ValueError("issued_from must be before or equal to issued_to")
        return self


QueryText = Annotated[str, Field(min_length=3, max_length=4000)]


class ResolveHints(StrictModel):
    document_id: str | None = None
    document_number: str | None = None


class ResolveRequest(StrictModel):
    reference: QueryText
    hints: ResolveHints = Field(default_factory=ResolveHints)
    limit: int = Field(default=5, ge=1, le=20)


class BatchGetRequest(StrictModel):
    ids: list[str] = Field(min_length=1, max_length=100)
    include_ancestors: bool = True
    include_relations: bool = False
    relation_status: RelationStatus = RelationStatus.VERIFIED


class SemanticSearchRequest(StrictModel):
    query: QueryText
    index: Literal["legal_node_embedding", "article_comparison_embedding", "behavior_embedding"] = (
        "legal_node_embedding"
    )
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.65, ge=-1, le=1)
    include_ancestors: bool = True


class SearchWeights(StrictModel):
    semantic: float = Field(default=0.7, ge=0, le=1)
    keyword: float = Field(default=0.3, ge=0, le=1)

    @model_validator(mode="after")
    def nonzero(self) -> "SearchWeights":
        if self.semantic + self.keyword <= 0:
            raise ValueError("at least one search weight must be positive")
        return self


class HybridSearchRequest(StrictModel):
    query: QueryText
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = Field(default=10, ge=1, le=50)
    candidate_k: int = Field(default=50, ge=1, le=200)
    weights: SearchWeights = Field(default_factory=SearchWeights)
    rerank: bool = False

    @model_validator(mode="after")
    def candidate_pool(self) -> "HybridSearchRequest":
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k")
        return self


class GraphExpandRequest(StrictModel):
    seed_ids: list[str] = Field(min_length=1, max_length=100)
    relationships: list[RelationshipType] = Field(
        default_factory=lambda: [RelationshipType.HAS_CHILD]
    )
    direction: Literal["OUTGOING", "INCOMING", "BOTH"] = "BOTH"
    depth: int = Field(default=1, ge=1, le=3)
    relationship_statuses: list[RelationStatus] = Field(
        default_factory=lambda: [RelationStatus.VERIFIED]
    )
    min_confidence: float = Field(default=0.85, ge=0, le=1)
    max_nodes: int = Field(default=100, ge=1, le=200)
    include_paths: bool = True


class RelationEndpointFilter(StrictModel):
    document_ids: list[str] = Field(default_factory=list, max_length=100)
    node_ids: list[str] = Field(default_factory=list, max_length=100)


class RelationsSearchRequest(StrictModel):
    source: RelationEndpointFilter = Field(default_factory=RelationEndpointFilter)
    target: RelationEndpointFilter = Field(default_factory=RelationEndpointFilter)
    types: list[RelationshipType] = Field(
        default_factory=lambda: [
            RelationshipType.THAY_THE,
            RelationshipType.SUA_DOI,
            RelationshipType.TUONG_UNG,
        ]
    )
    statuses: list[RelationStatus] = Field(default_factory=lambda: [RelationStatus.VERIFIED])
    min_confidence: float = Field(default=0.85, ge=0, le=1)
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


class BehaviorSearchRequest(StrictModel):
    query: QueryText
    document_ids: list[str] = Field(default_factory=list, max_length=100)
    statuses: list[RelationStatus] = Field(default_factory=lambda: [RelationStatus.VERIFIED])
    top_k: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.65, ge=-1, le=1)
    include_source: bool = True


class ComparisonSearchRequest(StrictModel):
    source_document_id: str
    target_document_id: str
    source_node_ids: list[str] = Field(default_factory=list, max_length=100)
    query: QueryText | None = None
    relationship_types: list[RelationshipType] = Field(
        default_factory=lambda: [
            RelationshipType.THAY_THE,
            RelationshipType.SUA_DOI,
            RelationshipType.TUONG_UNG,
        ]
    )
    statuses: list[RelationStatus] = Field(default_factory=lambda: [RelationStatus.VERIFIED])
    include_vector_candidates: bool = True
    top_k: int = Field(default=10, ge=1, le=50)


class RetrievalOptions(StrictModel):
    top_k: int = Field(default=12, ge=1, le=50)
    candidate_k: int = Field(default=50, ge=1, le=200)
    min_score: float = Field(default=0.6, ge=-1, le=1)
    rerank: bool = False


class RetrievalGraphOptions(StrictModel):
    enabled: bool = True
    relationships: list[RelationshipType] = Field(default_factory=lambda: list(RelationshipType))
    depth: int = Field(default=1, ge=1, le=3)
    relationship_statuses: list[RelationStatus] = Field(
        default_factory=lambda: [RelationStatus.VERIFIED]
    )
    min_confidence: float = Field(default=0.85, ge=0, le=1)
    max_nodes: int = Field(default=80, ge=1, le=200)


class ContextOptions(StrictModel):
    include_ancestors: bool = True
    include_siblings: bool = False
    include_full_article: bool = True
    token_budget: int = Field(default=12_000, ge=1, le=24_000)
    deduplicate: bool = True


class RetrievalQueryRequest(StrictModel):
    query: QueryText
    strategy: Literal["semantic", "hybrid", "graph", "auto"] = "auto"
    filters: SearchFilters = Field(default_factory=SearchFilters)
    retrieval: RetrievalOptions = Field(default_factory=RetrievalOptions)
    graph: RetrievalGraphOptions = Field(default_factory=RetrievalGraphOptions)
    context: ContextOptions = Field(default_factory=ContextOptions)
    debug: bool = False
