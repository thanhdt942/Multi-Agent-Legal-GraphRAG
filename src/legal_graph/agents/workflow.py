import copy
import json
import re
import uuid
from collections.abc import AsyncIterator
from typing import Any

from langgraph.graph import END, START, StateGraph

from legal_graph.application.agent_models import (
    AnswerConfidence,
    AnswerRequest,
    AnswerResponse,
    ClaimSupport,
    CriticDecision,
    CritiqueResult,
    DraftAnswer,
    ModelUsage,
    SituationAnalysis,
)
from legal_graph.application.models import (
    ComparisonSearchRequest,
    ContextOptions,
    CURRENT_VALIDITY_STATUSES,
    RetrievalGraphOptions,
    RetrievalOptions,
    RetrievalQueryRequest,
    RelationshipType,
)
from legal_graph.application.ports import ChatProvider
from legal_graph.application.services import RetrievalService
from legal_graph.core.config import Settings

from .prompts import ANSWER_SYNTHESIS_PROMPT, LEGAL_CRITIC_PROMPT, SITUATION_ANALYSIS_PROMPT
from .state import LegalAgentState

LAND_LAW_2024_ID = "177815"
LAND_LAW_2013_ID = "32833"
DISCLAIMER = "Thong tin chi co tinh chat ho tro tra cuu, khong thay the y kien chuyen mon phap ly."
CITATION_PATTERN = re.compile(r"\[(cit_[A-Za-z0-9_-]+)\]")
RAW_CITATION_PATTERN = re.compile(r"(?<!\[)\bcit_[A-Za-z0-9_-]+\b(?!\])")


def _usage_total(current: ModelUsage, added: ModelUsage) -> ModelUsage:
    return ModelUsage(
        input_tokens=current.input_tokens + added.input_tokens,
        output_tokens=current.output_tokens + added.output_tokens,
    )


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        default=lambda item: item.model_dump(mode="json"),
    )


def _prompt_contexts(retrieval: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "context_id": context["context_id"],
            "node_id": context["node"]["id"],
            "level": context["node"].get("level"),
            "text": context.get("text", ""),
            "source": context.get("source"),
            "citation_ids": context.get("citation_ids", []),
            "relationship_ids": context.get("relationship_ids", []),
            "warnings": context.get("warnings", []),
        }
        for context in retrieval.get("contexts", [])
    ]


def _prompt_comparisons(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_id": item.get("source", {}).get("id"),
            "target_id": item.get("target", {}).get("id"),
            "match_origin": item.get("match_origin"),
            "confidence": item.get("confidence"),
            "relationship": item.get("relationship"),
            "warnings": item.get("warnings", []),
        }
        for item in comparisons
    ]


class LegalAgentWorkflow:
    def __init__(
        self,
        retrieval: RetrievalService,
        chat: ChatProvider,
        settings: Settings,
        checkpointer: Any,
    ) -> None:
        self.retrieval = retrieval
        self.chat = chat
        self.settings = settings
        graph = StateGraph(LegalAgentState)
        graph.add_node("analyze_situation", self.analyze_situation)
        graph.add_node("retrieve_graph_evidence", self.retrieve_graph_evidence)
        graph.add_node("compare_historical_law", self.compare_historical_law)
        graph.add_node("synthesize_answer", self.synthesize_answer)
        graph.add_node("critique_answer", self.critique_answer)
        graph.add_node("finalize_answer", self.finalize_answer)
        graph.add_edge(START, "analyze_situation")
        graph.add_edge("analyze_situation", "retrieve_graph_evidence")
        graph.add_conditional_edges(
            "retrieve_graph_evidence",
            self.route_after_retrieval,
            {"compare": "compare_historical_law", "synthesize": "synthesize_answer"},
        )
        graph.add_edge("compare_historical_law", "synthesize_answer")
        graph.add_edge("synthesize_answer", "critique_answer")
        graph.add_conditional_edges(
            "critique_answer",
            self.route_after_critique,
            {
                "retrieve": "retrieve_graph_evidence",
                "compare": "compare_historical_law",
                "finalize": "finalize_answer",
            },
        )
        graph.add_edge("finalize_answer", END)
        self.graph = graph.compile(checkpointer=checkpointer)

    async def answer(self, request: AnswerRequest) -> AnswerResponse:
        final_answer = None
        async for event, data in self.answer_events(request):
            if event == "result":
                final_answer = AnswerResponse.model_validate(data)
        assert final_answer is not None
        return final_answer

    async def answer_events(
        self, request: AnswerRequest
    ) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex}"
        initial: LegalAgentState = {
            "request": request,
            "thread_id": thread_id,
            "analysis": None,
            "retrieval": None,
            "comparisons": [],
            "draft": None,
            "critique": None,
            "final_answer": None,
            "attempt": 0,
            "warnings": [],
            "usage": ModelUsage(),
        }
        config = {"configurable": {"thread_id": thread_id}}
        async for update in self.graph.astream(initial, config=config, stream_mode="updates"):
            for node_name, output in update.items():
                if node_name == "retrieve_graph_evidence":
                    retrieval = output.get("retrieval") or {}
                    yield (
                        "retrieval.completed",
                        {
                            "retrieval_id": retrieval.get("retrieval_id"),
                            "citation_count": len(retrieval.get("citations", [])),
                        },
                    )
                elif node_name in {
                    "analyze_situation",
                    "compare_historical_law",
                    "synthesize_answer",
                    "critique_answer",
                }:
                    yield "agent.completed", {"agent": node_name}
                elif node_name == "finalize_answer":
                    response = AnswerResponse.model_validate(output["final_answer"])
                    yield "result", response.model_dump(mode="json")

    async def analyze_situation(self, state: LegalAgentState) -> dict[str, Any]:
        request = state["request"]
        conversation = [message.model_dump() for message in request.messages]
        analysis, usage = await self.chat.generate_structured(
            [
                {"role": "system", "content": SITUATION_ANALYSIS_PROMPT},
                {
                    "role": "user",
                    "content": _json({"conversation": conversation, "question": request.question}),
                },
            ],
            SituationAnalysis,
            model=self.settings.openai_answer_model,
            temperature=0,
            max_output_tokens=900,
        )
        return {"analysis": analysis, "usage": _usage_total(state["usage"], usage)}

    async def retrieve_graph_evidence(self, state: LegalAgentState) -> dict[str, Any]:
        request = state["request"]
        analysis = state["analysis"]
        assert analysis is not None
        critique = state.get("critique")
        retry_queries = critique.missing_evidence_queries if critique else []
        query = (retry_queries or analysis.retrieval_queries or [request.question])[0]
        filters = request.retrieval.filters.model_copy(deep=True)
        question_lower = request.question.lower()
        if not filters.document_ids and (
            "dat dai" in question_lower or "đất đai" in question_lower
        ):
            filters.document_ids = [LAND_LAW_2024_ID]
        if analysis.requires_historical_comparison:
            filters.document_ids = list(
                dict.fromkeys([*filters.document_ids, LAND_LAW_2024_ID, LAND_LAW_2013_ID])
            )
            filters.validity_statuses = []
        else:
            filters.validity_statuses = list(CURRENT_VALIDITY_STATUSES)
        top_k = min(request.retrieval.top_k + state["attempt"] * 4, 50)
        result = await self.retrieval.retrieval_query(
            RetrievalQueryRequest(
                query=query,
                strategy=request.retrieval.strategy,
                filters=filters,
                retrieval=RetrievalOptions(
                    top_k=top_k,
                    candidate_k=max(top_k, min(top_k * 5, 200)),
                ),
                graph=RetrievalGraphOptions(
                    relationships=(
                        list(RelationshipType)
                        if analysis.requires_historical_comparison
                        else [
                            RelationshipType.HAS_CHILD,
                            RelationshipType.DAN_CHIEU,
                            RelationshipType.THAY_THE,
                            RelationshipType.SUA_DOI,
                            RelationshipType.LAM_HET_HIEU_LUC,
                        ]
                    ),
                    relationship_statuses=request.retrieval.relationship_statuses
                ),
                context=ContextOptions(
                    include_full_article=False,
                    token_budget=request.retrieval.context_token_budget,
                ),
            )
        )
        return {"retrieval": result, "critique": None}

    def route_after_retrieval(self, state: LegalAgentState) -> str:
        analysis = state["analysis"]
        if analysis and analysis.requires_historical_comparison and not state["comparisons"]:
            return "compare"
        return "synthesize"

    async def compare_historical_law(self, state: LegalAgentState) -> dict[str, Any]:
        request = state["request"]
        retrieval = copy.deepcopy(state["retrieval"] or {})
        source_ids = [
            context["node"]["id"]
            for context in retrieval.get("contexts", [])
            if context["node"].get("document_id") == LAND_LAW_2024_ID
            and context["node"].get("level") == "article"
        ]
        comparison = await self.retrieval.comparisons(
            ComparisonSearchRequest(
                source_document_id=LAND_LAW_2024_ID,
                target_document_id=LAND_LAW_2013_ID,
                source_node_ids=source_ids[:20],
                query=request.question,
                statuses=request.retrieval.relationship_statuses,
                include_vector_candidates=True,
                top_k=min(request.retrieval.top_k, 20),
            )
        )
        citations = retrieval.setdefault("citations", [])
        contexts = retrieval.setdefault("contexts", [])
        citation_by_node = {item["node_id"]: item["citation_id"] for item in citations}
        for item in comparison["items"]:
            relationship_id = (item.get("relationship") or {}).get("id")
            for side in ("source", "target"):
                citation = item.get(f"{side}_citation")
                node = item.get(side)
                if not citation or not node:
                    continue
                citation_id = citation_by_node.get(citation["node_id"])
                if citation_id is None:
                    citation_id = f"cit_{len(citations) + 1:02d}"
                    citation = {**citation, "citation_id": citation_id}
                    citations.append(citation)
                    citation_by_node[citation["node_id"]] = citation_id
                if not any(context["node"]["id"] == node["id"] for context in contexts):
                    contexts.append(
                        {
                            "context_id": f"ctx_{len(contexts) + 1:02d}",
                            "node": node,
                            "text": citation.get("quote", ""),
                            "score": item.get("confidence") or 0,
                            "source": "HISTORICAL_COMPARISON",
                            "citation_ids": [citation_id],
                            "relationship_ids": [relationship_id] if relationship_id else [],
                            "warnings": item.get("warnings", []),
                        }
                    )
        retrieval["warnings"] = list(
            dict.fromkeys(
                [
                    *retrieval.get("warnings", []),
                    *(
                        warning
                        for item in comparison["items"]
                        for warning in item.get("warnings", [])
                    ),
                ]
            )
        )
        return {"comparisons": comparison["items"], "retrieval": retrieval, "critique": None}

    async def synthesize_answer(self, state: LegalAgentState) -> dict[str, Any]:
        request = state["request"]
        retrieval = state["retrieval"] or {}
        if not retrieval.get("citations"):
            return {
                "draft": DraftAnswer(
                    answer="Khong tim thay du can cu trong du lieu de tra loi cau hoi nay.",
                    claims=[],
                    confidence=AnswerConfidence.LOW,
                    abstained=True,
                )
            }
        evidence = {
            "question": request.question,
            "analysis": state["analysis"],
            "contexts": _prompt_contexts(retrieval),
            "citations": retrieval.get("citations", []),
            "comparisons": _prompt_comparisons(state["comparisons"]),
            "warnings": retrieval.get("warnings", []),
            "format": request.generation.format,
        }
        draft, usage = await self.chat.generate_structured(
            [
                {"role": "system", "content": ANSWER_SYNTHESIS_PROMPT},
                {"role": "user", "content": _json(evidence)},
            ],
            DraftAnswer,
            model=self.settings.openai_answer_model,
            temperature=request.generation.temperature,
            max_output_tokens=request.generation.max_output_tokens,
        )
        return {"draft": draft, "usage": _usage_total(state["usage"], usage)}

    async def critique_answer(self, state: LegalAgentState) -> dict[str, Any]:
        request = state["request"]
        retrieval = state["retrieval"] or {}
        draft = state["draft"]
        assert draft is not None
        valid_citations = {item["citation_id"] for item in retrieval.get("citations", [])}
        deterministic_findings = []
        inline_citations = CITATION_PATTERN.findall(draft.answer)
        unknown_inline = set(inline_citations) - valid_citations
        if unknown_inline:
            deterministic_findings.append(
                f"Answer references unknown citations: {', '.join(sorted(unknown_inline))}"
            )
        if RAW_CITATION_PATTERN.search(draft.answer):
            deterministic_findings.append("Answer contains citations outside exact [cit_XX] syntax")
        if request.generation.require_citations and draft.claims and not inline_citations:
            deterministic_findings.append("Answer has substantive claims without inline citations")
        context_text_by_node = {
            context["node"]["id"]: context.get("text", "")
            for context in retrieval.get("contexts", [])
        }
        for citation in retrieval.get("citations", []):
            quote = citation.get("quote", "").strip()
            source_text = context_text_by_node.get(citation["node_id"], "")
            if quote and source_text and quote not in source_text and source_text not in quote:
                deterministic_findings.append(
                    f"Citation quote does not match retrieved context: {citation['citation_id']}"
                )
        for claim in draft.claims:
            unknown = set(claim.citation_ids) - valid_citations
            if unknown:
                deterministic_findings.append(
                    f"Claim references unknown citations: {', '.join(sorted(unknown))}"
                )
            if request.generation.require_citations and (
                not claim.citation_ids or claim.support == ClaimSupport.UNSUPPORTED
            ):
                deterministic_findings.append("A substantive claim is not supported by citations")
        critique, usage = await self.chat.generate_structured(
            [
                {"role": "system", "content": LEGAL_CRITIC_PROMPT},
                {
                    "role": "user",
                    "content": _json(
                        {
                            "question": request.question,
                            "draft": draft,
                            "citations": retrieval.get("citations", []),
                            "contexts": _prompt_contexts(retrieval),
                            "warnings": retrieval.get("warnings", []),
                            "deterministic_findings": deterministic_findings,
                        }
                    ),
                },
            ],
            CritiqueResult,
            model=self.settings.openai_critic_model,
            temperature=0,
            max_output_tokens=700,
        )
        findings = list(dict.fromkeys([*deterministic_findings, *critique.findings]))
        decision = critique.decision
        attempt = state["attempt"] + 1
        if deterministic_findings and decision == CriticDecision.PASS:
            decision = CriticDecision.RETRIEVE_MORE
        if attempt >= self.settings.agent_max_critique_attempts and decision not in {
            CriticDecision.PASS,
            CriticDecision.ABSTAIN,
        }:
            decision = CriticDecision.ABSTAIN
            findings.append("Maximum legal critique attempts reached")
        return {
            "critique": critique.model_copy(update={"decision": decision, "findings": findings}),
            "attempt": attempt,
            "usage": _usage_total(state["usage"], usage),
        }

    @staticmethod
    def route_after_critique(state: LegalAgentState) -> str:
        decision = state["critique"].decision if state["critique"] else CriticDecision.ABSTAIN
        if decision == CriticDecision.RETRIEVE_MORE:
            return "retrieve"
        if decision == CriticDecision.COMPARE_MORE:
            return "compare"
        return "finalize"

    async def finalize_answer(self, state: LegalAgentState) -> dict[str, Any]:
        request = state["request"]
        retrieval = state["retrieval"] or {}
        draft = state["draft"]
        critique = state["critique"]
        assert draft is not None
        abstained = draft.abstained or bool(
            critique and critique.decision == CriticDecision.ABSTAIN
        )
        if abstained:
            answer = "Khong du can cu phap ly trong du lieu de dua ra cau tra loi dang tin cay."
            claims = []
            confidence = AnswerConfidence.LOW
        else:
            answer = draft.answer
            claims = draft.claims
            confidence = draft.confidence
        citation_by_id = {
            citation["citation_id"]: citation for citation in retrieval.get("citations", [])
        }
        used_citation_ids = list(dict.fromkeys(CITATION_PATTERN.findall(answer)))
        citations = [citation_by_id[citation_id] for citation_id in used_citation_ids]
        warnings = list(
            dict.fromkeys(
                [
                    *state["warnings"],
                    *retrieval.get("warnings", []),
                    *(critique.findings if critique and abstained else []),
                    DISCLAIMER,
                ]
            )
        )
        response = AnswerResponse(
            answer_id=f"ans_{uuid.uuid4().hex}",
            thread_id=state["thread_id"],
            retrieval_id=retrieval.get("retrieval_id"),
            answer=answer,
            citations=citations,
            claims=claims,
            confidence=confidence,
            abstained=abstained,
            warnings=warnings,
            usage=state["usage"],
            retrieval=retrieval if request.include_retrieval else None,
        )
        return {"final_answer": response}
