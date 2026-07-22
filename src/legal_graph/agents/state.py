from typing import Any, TypedDict

from legal_graph.application.agent_models import (
    AnswerRequest,
    AnswerResponse,
    CritiqueResult,
    DraftAnswer,
    ModelUsage,
    SituationAnalysis,
)


class LegalAgentState(TypedDict):
    request: AnswerRequest
    thread_id: str
    analysis: SituationAnalysis | None
    retrieval: dict[str, Any] | None
    comparisons: list[dict[str, Any]]
    draft: DraftAnswer | None
    critique: CritiqueResult | None
    final_answer: AnswerResponse | None
    attempt: int
    warnings: list[str]
    usage: ModelUsage
