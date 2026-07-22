import json
from datetime import date, datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from legal_graph import __version__
from legal_graph.agents import LegalAgentWorkflow
from legal_graph.application.agent_models import AnswerRequest, AnswerResponse
from legal_graph.application.models import (
    BatchGetRequest,
    BehaviorSearchRequest,
    ComparisonSearchRequest,
    GraphExpandRequest,
    HybridSearchRequest,
    RelationStatus,
    RelationsSearchRequest,
    ResolveRequest,
    RetrievalQueryRequest,
    SemanticSearchRequest,
)
from legal_graph.application.services import RetrievalService
from legal_graph.core.errors import not_found
from legal_graph.http.dependencies import get_agent_workflow, get_repository, get_service
from legal_graph.infrastructure.neo4j_repository import Neo4jLegalGraphRepository


router = APIRouter(prefix="/v1")
Repository = Annotated[Neo4jLegalGraphRepository, Depends(get_repository)]
Service = Annotated[RetrievalService, Depends(get_service)]
AgentWorkflow = Annotated[LegalAgentWorkflow, Depends(get_agent_workflow)]


def sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/health")
async def health(repository: Repository, service: Service, agent: AgentWorkflow) -> Any:
    neo4j_ok = await repository.health()
    body = {
        "status": "ok" if neo4j_ok else "degraded",
        "version": __version__,
        "dependencies": {
            "neo4j": "ok" if neo4j_ok else "unavailable",
            "embedding_provider": "ok" if await service.embeddings.health() else "unavailable",
            "answer_model": "ok" if await agent.chat.health() else "unavailable",
        },
        "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return body if neo4j_ok else JSONResponse(body, status_code=503)


@router.get("/capabilities")
async def capabilities(service: Service) -> dict[str, Any]:
    return {
        "retrieval_strategies": ["semantic", "hybrid", "graph", "auto"],
        "supported_levels": ["document", "chapter", "section", "article", "clause", "point"],
        "supported_relationships": [
            "HAS_CHILD",
            "THAY_THE",
            "SUA_DOI",
            "TUONG_UNG",
            "DAN_CHIEU",
            "AP_DUNG_CHUYEN_TIEP",
            "LAM_HET_HIEU_LUC",
            "VI_PHAM",
        ],
        "embedding": {
            "model": service.embeddings.model,
            "dimensions": service.embeddings.dimensions,
        },
        "limits": {"max_top_k": 50, "max_graph_depth": 3, "max_context_tokens": 24_000},
        "answering": {
            "langgraph": True,
            "streaming": True,
            "historical_comparison_scope": ["177815", "32833"],
        },
    }


@router.get("/graph/schema")
async def graph_schema(repository: Repository, include_counts: bool = False) -> dict[str, Any]:
    return await repository.schema(include_counts)


@router.get("/documents")
async def list_documents(
    repository: Repository,
    q: str | None = Query(default=None, max_length=500),
    document_type: str | None = None,
    validity_status: str | None = None,
    issuing_authority: str | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
) -> dict[str, Any]:
    return await repository.list_documents(
        q=q,
        document_type=document_type,
        validity_status=validity_status,
        issuing_authority=issuing_authority,
        issued_from=issued_from,
        issued_to=issued_to,
        limit=limit,
        cursor=cursor,
    )


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    repository: Repository,
    include_relations: bool = False,
    relation_status: RelationStatus = RelationStatus.VERIFIED,
) -> dict[str, Any]:
    result = await repository.get_document(
        document_id, include_relations=include_relations, relation_status=relation_status.value
    )
    if not result:
        raise not_found("DOCUMENT")
    return result


@router.get("/documents/{document_id}/outline")
async def document_outline(
    document_id: str,
    repository: Repository,
    depth: int = Query(default=3, ge=1, le=4),
    include_content: bool = False,
) -> dict[str, Any]:
    result = await repository.outline(document_id, depth, include_content)
    if not result:
        raise not_found("DOCUMENT")
    return result


@router.post("/legal-nodes:resolve")
async def resolve_node(body: ResolveRequest, service: Service) -> dict[str, Any]:
    return await service.resolve(body)


@router.post("/legal-nodes:batch-get")
async def batch_get(body: BatchGetRequest, repository: Repository) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for node_id in dict.fromkeys(body.ids):
        item = await repository.get_node(
            node_id,
            include_ancestors=body.include_ancestors,
            include_relations=body.include_relations,
            relation_status=body.relation_status.value,
        )
        if item:
            found[node_id] = item
    return {
        "items": [found[node_id] for node_id in body.ids if node_id in found],
        "not_found": [node_id for node_id in body.ids if node_id not in found],
    }


@router.get("/legal-nodes/{node_id}/context")
async def node_context(
    node_id: str,
    repository: Repository,
    ancestors: bool = True,
    descendant_depth: int = Query(default=1, ge=0, le=3),
    siblings: bool = False,
    include_content: bool = True,
    max_nodes: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    result = await repository.context(
        node_id,
        ancestors=ancestors,
        descendant_depth=descendant_depth,
        siblings=siblings,
        include_content=include_content,
        max_nodes=max_nodes,
    )
    if not result:
        raise not_found("LEGAL_NODE")
    return result


@router.get("/legal-nodes/{node_id}")
async def get_node(
    node_id: str,
    repository: Repository,
    include_ancestors: bool = True,
    include_children: bool = False,
    include_relations: bool = False,
    relation_status: RelationStatus = RelationStatus.VERIFIED,
) -> dict[str, Any]:
    result = await repository.get_node(
        node_id,
        include_ancestors=include_ancestors,
        include_children=include_children,
        include_relations=include_relations,
        relation_status=relation_status.value,
    )
    if not result:
        raise not_found("LEGAL_NODE")
    return result


@router.post("/search/semantic")
async def semantic_search(body: SemanticSearchRequest, service: Service) -> dict[str, Any]:
    return await service.semantic_search(body)


@router.post("/search/hybrid")
async def hybrid_search(body: HybridSearchRequest, service: Service) -> dict[str, Any]:
    return await service.hybrid_search(body)


@router.post("/graph/expand")
async def expand_graph(body: GraphExpandRequest, service: Service) -> dict[str, Any]:
    return await service.expand(body)


@router.post("/relations/search")
async def relations_search(body: RelationsSearchRequest, service: Service) -> dict[str, Any]:
    return await service.relations(body)


@router.post("/behaviors/search")
async def behaviors_search(body: BehaviorSearchRequest, service: Service) -> dict[str, Any]:
    return await service.behaviors(body)


@router.post("/legal-comparisons/search")
async def comparisons_search(body: ComparisonSearchRequest, service: Service) -> dict[str, Any]:
    return await service.comparisons(body)


@router.post("/retrieval/query")
async def retrieval_query(body: RetrievalQueryRequest, service: Service) -> dict[str, Any]:
    return await service.retrieval_query(body)


@router.post("/answers", response_model=AnswerResponse)
async def answer_question(body: AnswerRequest, agent: AgentWorkflow) -> AnswerResponse:
    return await agent.answer(body)


@router.post("/answers:stream")
async def stream_answer(
    body: AnswerRequest, agent: AgentWorkflow, request: Request
) -> StreamingResponse:
    async def events() -> Any:
        try:
            async for event, data in agent.answer_events(body):
                if await request.is_disconnected():
                    return
                if event != "result":
                    yield sse_event(event, data)
                    continue
                response = AnswerResponse.model_validate(data)
                for citation in response.citations:
                    yield sse_event(
                        "citation",
                        {
                            "citation_id": citation.citation_id,
                            "citation": citation.model_dump(mode="json"),
                        },
                    )
                for start in range(0, len(response.answer), 160):
                    if await request.is_disconnected():
                        return
                    yield sse_event("answer.delta", {"text": response.answer[start : start + 160]})
                yield sse_event(
                    "answer.completed",
                    {
                        "answer_id": response.answer_id,
                        "thread_id": response.thread_id,
                        "confidence": response.confidence,
                        "abstained": response.abstained,
                        "claims": [claim.model_dump(mode="json") for claim in response.claims],
                        "warnings": response.warnings,
                        "usage": response.usage.model_dump(mode="json"),
                    },
                )
        except Exception as error:
            yield sse_event(
                "error",
                {
                    "code": getattr(error, "code", "INTERNAL_ERROR"),
                    "message": getattr(error, "message", "Answer generation failed"),
                    "retryable": getattr(error, "retryable", False),
                },
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
