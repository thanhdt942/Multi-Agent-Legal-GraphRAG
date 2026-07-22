from typing import Any

import pytest

from legal_graph.application.models import (
    ContextOptions,
    HybridSearchRequest,
    RetrievalOptions,
    RetrievalQueryRequest,
    SearchFilters,
    SemanticSearchRequest,
)
from legal_graph.application.services import RetrievalService


class FakeEmbeddings:
    model = "test-model"
    dimensions = 3

    async def embed(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class FakeRepository:
    min_score: float | None = None

    async def vector_search(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        self.min_score = args[4]
        return [{"node_id": "semantic", "score": 0.9}, {"node_id": "both", "score": 0.8}]

    async def keyword_search(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [{"node_id": "exact", "score": 10.0}, {"node_id": "both", "score": 5.0}]

    async def hydrate_hits(
        self, hits: list[dict[str, Any]], include_ancestors: bool = True
    ) -> list[dict[str, Any]]:
        return [
            {
                **hit,
                "node": {"id": hit["node_id"], "content": hit["node_id"]},
                "matched_text": hit["node_id"],
                "citation": None,
                "warnings": [],
            }
            for hit in hits
        ]

    async def hydrate_behavior_hits(
        self, hits: list[dict[str, Any]], include_source: bool = True
    ) -> list[dict[str, Any]]:
        return [
            {
                **hit,
                "node": {"id": f"hanh_vi:{hit['node_id']}", "canonical_text": hit["node_id"]},
                "matched_text": hit["node_id"],
                "citation": None,
                "warnings": [],
            }
            for hit in hits
        ]


class GraphRepository(FakeRepository):
    async def vector_search(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [{"node_id": "seed", "score": 0.9}]

    async def hydrate_hits(
        self, hits: list[dict[str, Any]], include_ancestors: bool = True
    ) -> list[dict[str, Any]]:
        return [
            {
                **hit,
                "node": {
                    "id": hit["node_id"],
                    "document_id": "177815",
                    "level": "article",
                    "content": hit["node_id"],
                },
                "matched_text": hit["node_id"],
                "citation": {
                    "node_id": hit["node_id"],
                    "document_id": "177815",
                    "article": "11",
                    "display": "Dieu 11",
                    "quote": hit["node_id"],
                    "validity_status": "Hết hiệu lực một phần",
                },
                "warnings": [],
            }
            for hit in hits
        ]

    async def expand(self, request: Any) -> dict[str, Any]:
        return {
            "nodes": [{"id": "seed"}, {"id": "related"}],
            "relationships": [
                {
                    "id": "rel_01",
                    "type": "DAN_CHIEU",
                    "source_id": "seed",
                    "target_id": "related",
                    "warnings": [],
                }
            ],
            "paths": [
                {
                    "node_ids": ["seed", "related"],
                    "relationship_types": ["DAN_CHIEU"],
                    "length": 1,
                }
            ],
            "truncated": False,
            "warnings": [],
        }


class ExpiredGraphRepository(GraphRepository):
    async def hydrate_hits(
        self, hits: list[dict[str, Any]], include_ancestors: bool = True
    ) -> list[dict[str, Any]]:
        hydrated = await super().hydrate_hits(hits, include_ancestors)
        for hit in hydrated:
            hit["citation"]["validity_status"] = (
                "Hết hiệu lực toàn bộ"
                if hit["node"]["id"] == "related"
                else "Hết hiệu lực một phần"
            )
        return hydrated


class SupersededGraphRepository(ExpiredGraphRepository):
    async def hydrate_hits(
        self, hits: list[dict[str, Any]], include_ancestors: bool = True
    ) -> list[dict[str, Any]]:
        hydrated = await GraphRepository.hydrate_hits(self, hits, include_ancestors)
        for hit in hydrated:
            hit["citation"]["validity_status"] = "Hết hiệu lực một phần"
        return hydrated

    async def expand(self, request: Any) -> dict[str, Any]:
        graph = await super().expand(request)
        graph["relationships"][0]["type"] = "THAY_THE"
        return graph


@pytest.mark.asyncio
async def test_hybrid_keeps_exact_keyword_result() -> None:
    service = RetrievalService(FakeRepository(), FakeEmbeddings())  # type: ignore[arg-type]
    result = await service.hybrid_search(
        HybridSearchRequest(query="exact legal phrase", top_k=3, candidate_k=3)
    )
    ids = [hit["node"]["id"] for hit in result["hits"]]
    assert "exact" in ids
    assert result["meta"]["fusion"] == "RRF(k=60)"


@pytest.mark.asyncio
async def test_semantic_behavior_index_hydrates_behavior_nodes() -> None:
    repository = FakeRepository()
    service = RetrievalService(repository, FakeEmbeddings())  # type: ignore[arg-type]
    result = await service.semantic_search(
        SemanticSearchRequest(
            query="hanh vi lan chiem dat",
            index="behavior_embedding",
            min_score=0.42,
            top_k=1,
        )
    )
    assert result["hits"][0]["node"]["id"] == "hanh_vi:semantic"
    assert repository.min_score == 0.42


@pytest.mark.asyncio
async def test_graph_expansion_adds_cited_context() -> None:
    service = RetrievalService(GraphRepository(), FakeEmbeddings())  # type: ignore[arg-type]
    result = await service.retrieval_query(
        RetrievalQueryRequest(
            query="quy dinh lien quan",
            strategy="semantic",
            retrieval=RetrievalOptions(top_k=1, candidate_k=1),
            context=ContextOptions(include_full_article=False),
        )
    )
    related = next(context for context in result["contexts"] if context["node"]["id"] == "related")
    assert related["source"] == "GRAPH"
    assert related["citation_ids"]
    assert related["relationship_ids"] == ["rel_01"]


@pytest.mark.asyncio
async def test_graph_expansion_excludes_expired_documents() -> None:
    service = RetrievalService(ExpiredGraphRepository(), FakeEmbeddings())  # type: ignore[arg-type]
    result = await service.retrieval_query(
        RetrievalQueryRequest(
            query="quy dinh hien hanh",
            strategy="semantic",
            filters=SearchFilters(
                validity_statuses=["Còn hiệu lực", "Hết hiệu lực một phần"]
            ),
            retrieval=RetrievalOptions(top_k=1, candidate_k=1),
            context=ContextOptions(include_full_article=False),
        )
    )

    assert [context["node"]["id"] for context in result["contexts"]] == ["seed"]
    assert [citation["node_id"] for citation in result["citations"]] == ["seed"]


@pytest.mark.asyncio
async def test_current_retrieval_excludes_superseded_provision() -> None:
    service = RetrievalService(SupersededGraphRepository(), FakeEmbeddings())  # type: ignore[arg-type]
    result = await service.retrieval_query(
        RetrievalQueryRequest(
            query="quy dinh hien hanh",
            strategy="semantic",
            filters=SearchFilters(
                validity_statuses=["Còn hiệu lực", "Hết hiệu lực một phần"]
            ),
            retrieval=RetrievalOptions(top_k=1, candidate_k=1),
            context=ContextOptions(include_full_article=False),
        )
    )

    assert [context["node"]["id"] for context in result["contexts"]] == ["seed"]
    assert [citation["node_id"] for citation in result["citations"]] == ["seed"]
