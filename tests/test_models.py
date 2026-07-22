import pytest
from pydantic import ValidationError

from legal_graph.application.models import (
    GraphExpandRequest,
    HybridSearchRequest,
    RetrievalQueryRequest,
    SearchFilters,
    SemanticSearchRequest,
)


def test_index_allowlist_rejects_cypher_injection() -> None:
    with pytest.raises(ValidationError):
        SemanticSearchRequest(query="tim quy dinh", index="x') MATCH (n) RETURN n //")


def test_relationship_allowlist_rejects_wildcard() -> None:
    with pytest.raises(ValidationError):
        GraphExpandRequest(seed_ids=["node"], relationships=["*"])


def test_graph_bounds_are_enforced() -> None:
    with pytest.raises(ValidationError):
        GraphExpandRequest(seed_ids=["node"], depth=4)
    with pytest.raises(ValidationError):
        GraphExpandRequest(seed_ids=["node"], max_nodes=201)


def test_hybrid_candidate_pool_covers_top_k() -> None:
    with pytest.raises(ValidationError):
        HybridSearchRequest(query="tim quy dinh", top_k=20, candidate_k=10)


def test_retrieval_candidate_pool_covers_top_k() -> None:
    with pytest.raises(ValidationError):
        RetrievalQueryRequest(
            query="tim quy dinh",
            retrieval={"top_k": 20, "candidate_k": 10},
        )


def test_search_defaults_to_currently_applicable_documents() -> None:
    assert SearchFilters().validity_statuses == ["Còn hiệu lực", "Hết hiệu lực một phần"]
    assert SearchFilters(validity_statuses=[]).validity_statuses == []
