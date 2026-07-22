import time
import uuid
from typing import Any

import tiktoken

from .models import (
    BehaviorSearchRequest,
    ComparisonSearchRequest,
    GraphExpandRequest,
    HybridSearchRequest,
    RelationsSearchRequest,
    ResolveRequest,
    RetrievalQueryRequest,
    SemanticSearchRequest,
    SearchFilters,
)
from .ports import EmbeddingProvider, LegalGraphRepository


PROPOSED_WARNING = "Quan he PROPOSED chua duoc chuyen gia phap ly phe duyet"
SOURCE_METADATA_WARNING = "SOURCE_METADATA: Quan he nguon khong co thong tin trang thai"
SUPERSEDING_RELATIONSHIPS = {"THAY_THE", "SUA_DOI", "LAM_HET_HIEU_LUC"}


def _hit_matches_filters(hit: dict[str, Any], filters: SearchFilters) -> bool:
    """Reapply document filters to nodes added after the initial search."""
    node = hit.get("node", {})
    citation = hit.get("citation") or {}
    if filters.document_ids and citation.get("document_id") not in filters.document_ids:
        return False
    if filters.document_numbers and citation.get("document_number") not in filters.document_numbers:
        return False
    if filters.levels and node.get("level") not in filters.levels:
        return False
    if (
        filters.validity_statuses
        and citation.get("validity_status") not in filters.validity_statuses
    ):
        return False
    return True


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
        if request.index == "behavior_embedding":
            hits = await self.repository.hydrate_behavior_hits(
                candidates[: request.top_k], request.include_ancestors
            )
        else:
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
            request.min_score,
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
        elif strategy == "hybrid":
            result = await self.hybrid_search(
                HybridSearchRequest(
                    query=request.query,
                    filters=request.filters,
                    top_k=request.retrieval.top_k,
                    candidate_k=request.retrieval.candidate_k,
                    min_score=request.retrieval.min_score,
                    rerank=request.retrieval.rerank,
                )
            )
        elif strategy == "graph":
            resolved = await self.resolve(ResolveRequest(reference=request.query, limit=12))
            seeds = [
                {"node_id": item["node"]["id"], "score": item["confidence"]}
                for item in resolved["matches"]
            ]
            hits = await self.repository.hydrate_hits(
                seeds[: request.retrieval.top_k], request.context.include_ancestors
            )
            for hit in hits:
                hit["scores"] = {
                    "vector": None,
                    "keyword": None,
                    "reranker": None,
                    "final": hit["score"],
                }
            result = {
                "query": request.query,
                "hits": hits,
                "meta": {"candidate_count": len(seeds), "index": None},
            }
        else:  # guarded by Pydantic, retained for non-HTTP callers
            raise ValueError(f"Unsupported strategy: {strategy}")

        hits = result["hits"]
        extra_scores: dict[str, float] = {}
        for hit in hits:
            if request.context.include_full_article:
                article = next(
                    (
                        node
                        for node in [hit["node"], *hit.get("ancestors", [])]
                        if node.get("level") == "article"
                    ),
                    None,
                )
                if article:
                    article_context = await self.repository.context(
                        article["id"],
                        ancestors=False,
                        descendant_depth=2,
                        siblings=False,
                        include_content=True,
                        max_nodes=100,
                    )
                    if article_context:
                        for node in [
                            article_context["node"],
                            *article_context.get("related_nodes", []),
                        ]:
                            extra_scores.setdefault(node["id"], hit["score"])
            if request.context.include_siblings:
                sibling_context = await self.repository.context(
                    hit["node"]["id"],
                    ancestors=False,
                    descendant_depth=0,
                    siblings=True,
                    include_content=True,
                    max_nodes=20,
                )
                if sibling_context:
                    for node in sibling_context.get("related_nodes", []):
                        extra_scores.setdefault(node["id"], hit["score"])
        existing_ids = {hit["node"]["id"] for hit in hits}
        if extra_scores:
            hits.extend(
                await self.repository.hydrate_hits(
                    [
                        {"node_id": node_id, "score": score}
                        for node_id, score in extra_scores.items()
                        if node_id not in existing_ids
                    ],
                    request.context.include_ancestors,
                )
            )
        if request.context.deduplicate:
            hits = list({hit["node"]["id"]: hit for hit in hits}.values())

        hits = [hit for hit in hits if _hit_matches_filters(hit, request.filters)]

        initial_ids = {hit["node"]["id"] for hit in hits}
        graph = {"nodes": [], "relationships": [], "paths": [], "truncated": False}
        if request.graph.enabled and hits:
            graph = await self.repository.expand(
                GraphExpandRequest(
                    seed_ids=[hit["node"]["id"] for hit in hits[:100]],
                    relationships=request.graph.relationships,
                    depth=request.graph.depth,
                    relationship_statuses=request.graph.relationship_statuses,
                    min_confidence=request.graph.min_confidence,
                    max_nodes=request.graph.max_nodes,
                    include_paths=True,
                )
            )

        graph_scores: dict[str, float] = {}
        hit_scores = {hit["node"]["id"]: hit["score"] for hit in hits}
        for path in graph.get("paths", []):
            node_ids = path.get("node_ids", [])
            seed_score = next(
                (hit_scores[node_id] for node_id in node_ids if node_id in hit_scores), 0
            )
            for distance, node_id in enumerate(node_ids):
                if node_id not in initial_ids:
                    graph_scores[node_id] = max(
                        graph_scores.get(node_id, 0), seed_score * (0.9 ** max(distance, 1))
                    )
        if graph_scores:
            hits.extend(
                await self.repository.hydrate_hits(
                    [
                        {"node_id": node_id, "score": score}
                        for node_id, score in graph_scores.items()
                    ],
                    request.context.include_ancestors,
                )
            )
            hits = list({hit["node"]["id"]: hit for hit in hits}.values())
            hits = [hit for hit in hits if _hit_matches_filters(hit, request.filters)]

        if request.filters.validity_statuses:
            superseded_ids = {
                relationship.get("target_id")
                for relationship in graph.get("relationships", [])
                if relationship.get("type") in SUPERSEDING_RELATIONSHIPS
            }
            hits = [hit for hit in hits if hit["node"]["id"] not in superseded_ids]

        citations: list[dict[str, Any]] = []
        citation_ids: dict[str, str] = {}
        contexts: list[dict[str, Any]] = []
        token_count = 0
        truncated = False
        try:
            encoding = tiktoken.encoding_for_model(self.embeddings.model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        relationship_ids_by_node: dict[str, list[str]] = {}
        for relationship in graph.get("relationships", []):
            relationship_id = relationship.get("id")
            if not relationship_id:
                continue
            for node_id in (relationship.get("source_id"), relationship.get("target_id")):
                if node_id:
                    relationship_ids_by_node.setdefault(node_id, []).append(relationship_id)
        for hit in hits:
            citation = hit.get("citation")
            if not citation:
                continue
            node_id = hit["node"]["id"]
            text = hit.get("matched_text") or hit["node"].get("content") or ""
            estimated = len(encoding.encode(text))
            if token_count + estimated > request.context.token_budget:
                truncated = True
                continue
            token_count += estimated
            citation_id = citation_ids.setdefault(node_id, f"cit_{len(citation_ids) + 1:02d}")
            if not any(item["citation_id"] == citation_id for item in citations):
                citation = {**citation, "citation_id": citation_id}
                citations.append(citation)
            if node_id not in initial_ids:
                source = "GRAPH"
            elif relationship_ids_by_node.get(node_id):
                source = "VECTOR_AND_GRAPH"
            elif hit.get("scores", {}).get("keyword") is not None:
                source = "HYBRID"
            else:
                source = "VECTOR"
            contexts.append(
                {
                    "context_id": f"ctx_{len(contexts) + 1:02d}",
                    "node": hit["node"],
                    "text": text,
                    "score": hit["score"],
                    "source": source,
                    "citation_ids": [citation_id],
                    "relationship_ids": relationship_ids_by_node.get(node_id, []),
                    "warnings": hit.get("warnings", []),
                }
            )

        warnings = list(dict.fromkeys(w for context in contexts for w in context["warnings"]))
        warnings.extend(w for w in graph.get("warnings", []) if w not in warnings)
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
                "articles": len(
                    {
                        (citation.get("document_id"), citation.get("article"))
                        for citation in citations
                        if citation.get("article")
                    }
                ),
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
