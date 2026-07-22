from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from legal_graph.agents.workflow import LegalAgentWorkflow
from legal_graph.application.agent_models import (
    AnswerRequest,
    CriticDecision,
    CritiqueResult,
    DraftAnswer,
    LegalClaim,
    ModelUsage,
    SituationAnalysis,
)
from legal_graph.core.config import Settings


class FakeChat:
    def __init__(
        self,
        *,
        compare: bool = False,
        invalid_first_draft: bool = False,
        malformed_first_draft: bool = False,
    ) -> None:
        self.compare = compare
        self.invalid_first_draft = invalid_first_draft
        self.malformed_first_draft = malformed_first_draft
        self.draft_calls = 0

    async def generate_structured(
        self, messages: list[dict[str, str]], response_model: type[Any], **kwargs: Any
    ) -> tuple[Any, ModelUsage]:
        if response_model is SituationAnalysis:
            result = SituationAnalysis(
                summary="Tranh chap dat dai",
                facts=["Nguoi dung hoi ve lan chiem dat"],
                legal_issues=["Hanh vi bi cam"],
                applicable_date=None,
                legal_references=[],
                retrieval_queries=["hanh vi lan chiem dat"],
                requires_historical_comparison=self.compare,
                missing_facts=[],
                should_abstain=False,
            )
        elif response_model is DraftAnswer:
            self.draft_calls += 1
            citation_id = (
                "cit_unknown" if self.invalid_first_draft and self.draft_calls == 1 else "cit_01"
            )
            answer = (
                "Hanh vi lan chiem dat bi nghiem cam (DIRECT: cit_01)."
                if self.malformed_first_draft and self.draft_calls == 1
                else "Hanh vi lan chiem dat bi nghiem cam [cit_01]."
            )
            result = DraftAnswer(
                answer=answer,
                claims=[
                    LegalClaim(
                        text="Lan chiem dat bi cam", citation_ids=[citation_id], support="DIRECT"
                    )
                ],
                confidence="HIGH",
                abstained=False,
            )
        else:
            result = CritiqueResult(decision=CriticDecision.PASS, findings=[])
        return result, ModelUsage(input_tokens=10, output_tokens=5)


class FakeRetrieval:
    def __init__(self) -> None:
        self.retrieval_calls = 0
        self.comparison_calls = 0
        self.requests: list[Any] = []

    async def retrieval_query(self, request: Any) -> dict[str, Any]:
        self.retrieval_calls += 1
        self.requests.append(request)
        return {
            "retrieval_id": f"ret_{self.retrieval_calls}",
            "contexts": [
                {
                    "context_id": "ctx_01",
                    "node": {
                        "id": "article_11",
                        "document_id": "177815",
                        "level": "article",
                    },
                    "text": "Nghiem cam lan dat, chiem dat.",
                    "score": 0.9,
                    "source": "VECTOR",
                    "citation_ids": ["cit_01"],
                    "relationship_ids": [],
                    "warnings": [],
                }
            ],
            "citations": [
                {
                    "citation_id": "cit_01",
                    "node_id": "article_11",
                    "document_id": "177815",
                    "document_name": "Luat Dat dai 2024",
                    "article": "11",
                    "display": "Dieu 11 Luat Dat dai 2024",
                    "quote": "Nghiem cam lan dat, chiem dat.",
                    "validity_status": "Hết hiệu lực một phần",
                },
                {
                    "citation_id": "cit_02",
                    "node_id": "article_12",
                    "document_id": "177815",
                    "document_name": "Luat Dat dai 2024",
                    "article": "12",
                    "display": "Dieu 12 Luat Dat dai 2024",
                    "quote": "Quy dinh khong duoc dung trong cau tra loi.",
                    "validity_status": "Hết hiệu lực một phần",
                },
            ],
            "graph": {"nodes": [], "relationships": [], "paths": []},
            "warnings": [],
        }

    async def comparisons(self, request: Any) -> dict[str, Any]:
        self.comparison_calls += 1
        return {"items": []}


def settings() -> Settings:
    return Settings(neo4j_auth="neo4j/password", openai_api_key="test")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_routes_through_historical_comparison() -> None:
    retrieval = FakeRetrieval()
    workflow = LegalAgentWorkflow(
        retrieval,
        FakeChat(compare=True),
        settings(),
        InMemorySaver(),  # type: ignore[arg-type]
    )
    response = await workflow.answer(
        AnswerRequest(question="Quy dinh nam 2024 thay doi gi so voi Luat Dat dai 2013?")
    )
    assert retrieval.comparison_calls == 1
    assert retrieval.requests[0].filters.validity_statuses == []
    assert response.abstained is False
    assert response.claims[0].citation_ids == ["cit_01"]
    assert response.usage.input_tokens == 30


@pytest.mark.asyncio
async def test_unknown_citation_forces_retrieval_retry() -> None:
    retrieval = FakeRetrieval()
    workflow = LegalAgentWorkflow(
        retrieval,
        FakeChat(invalid_first_draft=True),
        settings(),
        InMemorySaver(),  # type: ignore[arg-type]
    )
    response = await workflow.answer(AnswerRequest(question="Hanh vi lan chiem dat co bi cam?"))
    assert retrieval.retrieval_calls == 2
    assert response.abstained is False
    assert response.claims[0].citation_ids == ["cit_01"]


@pytest.mark.asyncio
async def test_current_law_filters_and_prunes_unused_citations() -> None:
    retrieval = FakeRetrieval()
    workflow = LegalAgentWorkflow(
        retrieval,
        FakeChat(),
        settings(),
        InMemorySaver(),  # type: ignore[arg-type]
    )

    response = await workflow.answer(AnswerRequest(question="Hanh vi lan chiem dat co bi cam?"))

    request = retrieval.requests[0]
    assert request.filters.validity_statuses == ["Còn hiệu lực", "Hết hiệu lực một phần"]
    assert request.context.include_full_article is False
    assert {relationship.value for relationship in request.graph.relationships} == {
        "HAS_CHILD",
        "DAN_CHIEU",
        "THAY_THE",
        "SUA_DOI",
        "LAM_HET_HIEU_LUC",
    }
    assert [citation.citation_id for citation in response.citations] == ["cit_01"]


@pytest.mark.asyncio
async def test_malformed_inline_citation_forces_retry() -> None:
    retrieval = FakeRetrieval()
    chat = FakeChat(malformed_first_draft=True)
    workflow = LegalAgentWorkflow(
        retrieval,
        chat,
        settings(),
        InMemorySaver(),  # type: ignore[arg-type]
    )

    response = await workflow.answer(AnswerRequest(question="Hanh vi lan chiem dat co bi cam?"))

    assert chat.draft_calls == 2
    assert response.answer.endswith("[cit_01].")
