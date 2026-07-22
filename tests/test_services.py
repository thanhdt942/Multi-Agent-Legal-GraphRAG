from typing import Any

import pytest

from legal_graph.application.models import HybridSearchRequest
from legal_graph.application.services import RetrievalService


class FakeEmbeddings:
    model = "test-model"
    dimensions = 3

    async def embed(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class FakeRepository:
    async def vector_search(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
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


@pytest.mark.asyncio
async def test_hybrid_keeps_exact_keyword_result() -> None:
    service = RetrievalService(FakeRepository(), FakeEmbeddings())  # type: ignore[arg-type]
    result = await service.hybrid_search(
        HybridSearchRequest(query="exact legal phrase", top_k=3, candidate_k=3)
    )
    ids = [hit["node"]["id"] for hit in result["hits"]]
    assert "exact" in ids
    assert result["meta"]["fusion"] == "RRF(k=60)"
