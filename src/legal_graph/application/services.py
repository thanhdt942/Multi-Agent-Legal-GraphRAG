import time
import uuid
from typing import Any

from .models import (
    BehaviorSearchRequest,
    ComparisonSearchRequest,
    GraphExpandRequest,
    HybridSearchRequest,
    RelationsSearchRequest,
    ResolveRequest,
    RetrievalQueryRequest,
    SemanticSearchRequest,
)
from .ports import EmbeddingProvider, LegalGraphRepository


PROPOSED_WARNING = "Quan he PROPOSED chua duoc chuyen gia phap ly phe duyet"
SOURCE_METADATA_WARNING = "SOURCE_METADATA: Quan he nguon khong co thong tin trang thai"


class RetrievalService:
    """Retrieval use cases shared by HTTP and future agent adapters."""

    def __init__(self, repository: LegalGraphRepository, embeddings: EmbeddingProvider) -> None:
        self.repository = repository
        self.embeddings = embeddings

    async def semantic_search(self, request: SemanticSearchRequest) -> dict[str, Any]:
        started = time.perf_counter()
        vector = await self.embeddings.embed(request.query)
        candidates = await self.repository.vector_search(
            vector,
            request.index,
            request.filters,
            max(request.top_k * 5, 50),
            request.min_score,
        )
        hits = await self.repository.hydrate_hits(
            candidates[: request.top_k], request.include_ancestors
        )
        for hit in hits:
            score = hit["score"]
            hit["scores"] = {
                "vector": score,
                "keyword": None,
                "reranker": None,
                "final": score,
            }
        return {
            "query": request.query,
            "hits": hits,
            "meta": {
                "index": request.index,
                "embedding_model": self.embeddings.model,
                "candidate_count": len(candidates),
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        }

    async def hybrid_search(self, request: HybridSearchRequest) -> dict[str, Any]:
        started = time.perf_counter()
        vector = await self.embeddings.embed(request.query)
        semantic = await self.repository.vector_search(
            vector,
            "legal_node_embedding",
            request.filters,
            request.candidate_k,
            -1,
        )
        keyword = await self.repository.keyword_search(
            request.query, request.filters, request.candidate_k
        )
        semantic_by_id = {item["node_id"]: (rank, item) for rank, item in enumerate(semantic, 1)}
        keyword_by_id = {item["node_id"]: (rank, item) for rank, item in enumerate(keyword, 1)}
        ids = semantic_by_id.keys() | keyword_by_id.keys()
        fused: list[dict[str, Any]] = []
        normalizer = request.weights.semantic + request.weights.keyword
        for node_id in ids:
            semantic_entry = semantic_by_id.get(node_id)
            keyword_entry = keyword_by_id.get(node_id)
            score = (
                request.weights.semantic / (60 + semantic_entry[0]) if semantic_entry else 0
            ) + (request.weights.keyword / (60 + keyword_entry[0]) if keyword_entry else 0)
            item = dict((semantic_entry or keyword_entry)[1])
            item["rrf_score"] = score / normalizer
            item["vector_score"] = semantic_entry[1]["score"] if semantic_entry else None
            item["keyword_score"] = keyword_entry[1]["score"] if keyword_entry else None
            fused.append(item)
        fused.sort(key=lambda item: item["rrf_score"], reverse=True)
        hits = await self.repository.hydrate_hits(fused[: request.top_k])
        for hit in hits:
            hit["score"] = hit.pop("rrf_score")
            hit["scores"] = {
                "vector": hit.pop("vector_score", None),
                "keyword": hit.pop("keyword_score", None),
                "reranker": None,
                "final": hit["score"],
            }
        return {
            "query": request.query,
            "hits": hits,
            "meta": {
                "index": "legal_node_embedding+legal_node_fulltext",
                "embedding_model": self.embeddings.model,
                "candidate_count": len(fused),
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "fusion": "RRF(k=60)",
                "reranked": False,
            },
        }

    async def resolve(self, request: ResolveRequest) -> dict[str, Any]:
        matches = await self.repository.resolve(request)
        return {"matches": matches, "ambiguous": len(matches) > 1}

    async def behaviors(self, request: BehaviorSearchRequest) -> dict[str, Any]:
        return await self.repository.behaviors(request, await self.embeddings.embed(request.query))

    async def comparisons(self, request: ComparisonSearchRequest) -> dict[str, Any]:
        embedding = None
        if request.include_vector_candidates and request.query:
            embedding = await self.embeddings.embed(request.query)
        return await self.repository.comparisons(request, embedding)

    async def retrieval_query(self, request: RetrievalQueryRequest) -> dict[str, Any]:
        started = time.perf_counter()
        strategy = "hybrid" if request.strategy == "auto" else request.strategy
        if strategy == "semantic":
            result = await self.semantic_search(
                SemanticSearchRequest(
                    query=request.query,
                    filters=request.filters,
                    top_k=request.retrieval.top_k,
                    min_score=request.retrieval.min_score,
                    include_ancestors=request.context.include_ancestors,
                )
            )
        elif strategy in {"hybrid", "graph"}:
            result = await self.hybrid_search(
                HybridSearchRequest(
                    query=request.query,
                    filters=request.filters,
                    top_k=request.retrieval.top_k,
                    candidate_k=request.retrieval.candidate_k,
                    rerank=request.retrieval.rerank,
                )
            )
        else:  # guarded by Pydantic, retained for non-HTTP callers
            raise ValueError(f"Unsupported strategy: {strategy}")

        hits = result["hits"]
        graph = {"nodes": [], "relationships": [], "paths": [], "truncated": False}
        if request.graph.enabled and hits:
            graph = await self.repository.expand(
                GraphExpandRequest(
                    seed_ids=[hit["node"]["id"] for hit in hits],
                    relationships=request.graph.relationships,
                    depth=request.graph.depth,
                    relationship_statuses=request.graph.relationship_statuses,
                    min_confidence=request.graph.min_confidence,
                    max_nodes=request.graph.max_nodes,
                    include_paths=True,
                )
            )

        citations: list[dict[str, Any]] = []
        citation_ids: dict[str, str] = {}
        contexts: list[dict[str, Any]] = []
        token_count = 0
        truncated = False
        for hit in hits:
            citation = hit.get("citation")
            if not citation:
                continue
            node_id = hit["node"]["id"]
            citation_id = citation_ids.setdefault(node_id, f"cit_{len(citation_ids) + 1:02d}")
            if not any(item["citation_id"] == citation_id for item in citations):
                citation = {**citation, "citation_id": citation_id}
                citations.append(citation)
            text = hit.get("matched_text") or hit["node"].get("content") or ""
            estimated = max(1, len(text) // 4)
            if token_count + estimated > request.context.token_budget:
                truncated = True
                continue
            token_count += estimated
            contexts.append(
                {
                    "context_id": f"ctx_{len(contexts) + 1:02d}",
                    "node": hit["node"],
                    "text": text,
                    "score": hit["score"],
                    "source": "VECTOR_AND_GRAPH" if graph["relationships"] else "VECTOR",
                    "citation_ids": [citation_id],
                    "relationship_ids": [],
                    "warnings": hit.get("warnings", []),
                }
            )

        warnings = list(dict.fromkeys(w for context in contexts for w in context["warnings"]))
        warnings.extend(w for w in graph.get("warnings", []) if w not in warnings)
        levels = {context["node"].get("level") for context in contexts}
        return {
            "retrieval_id": f"ret_{uuid.uuid4().hex}",
            "query": request.query,
            "strategy_used": f"{strategy}_graph" if request.graph.enabled else strategy,
            "contexts": contexts,
            "citations": citations,
            "graph": {key: graph[key] for key in ("nodes", "relationships", "paths")},
            "warnings": warnings,
            "coverage": {
                "documents": len({c["document_id"] for c in citations}),
                "articles": sum(level == "article" for level in levels),
                "context_tokens": token_count,
                "truncated": truncated or graph.get("truncated", False),
            },
            "trace": {
                "candidate_count": result["meta"]["candidate_count"],
                "context_count": len(contexts),
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }
            if request.debug
            else None,
        }

    async def expand(self, request: GraphExpandRequest) -> dict[str, Any]:
        return await self.repository.expand(request)

    async def relations(self, request: RelationsSearchRequest) -> dict[str, Any]:
        return await self.repository.relations(request)
