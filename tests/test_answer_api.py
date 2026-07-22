from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_graph.application.agent_models import AnswerResponse
from legal_graph.http.dependencies import get_agent_workflow
from legal_graph.http.v1.router import router


def answer_data() -> dict[str, Any]:
    return {
        "answer_id": "ans_test",
        "thread_id": "thread_test",
        "retrieval_id": "ret_test",
        "answer": "Lan chiem dat bi nghiem cam [cit_01].",
        "citations": [
            {
                "citation_id": "cit_01",
                "node_id": "article_11",
                "document_id": "177815",
                "display": "Dieu 11 Luat Dat dai 2024",
                "quote": "Nghiem cam lan dat, chiem dat.",
            }
        ],
        "claims": [
            {
                "text": "Lan chiem dat bi nghiem cam",
                "citation_ids": ["cit_01"],
                "support": "DIRECT",
            }
        ],
        "confidence": "HIGH",
        "abstained": False,
        "warnings": ["Legal research disclaimer"],
        "usage": {"input_tokens": 10, "output_tokens": 5},
        "retrieval": None,
    }


class FakeAgent:
    async def answer(self, body: Any) -> AnswerResponse:
        return AnswerResponse.model_validate(answer_data())

    async def answer_events(self, body: Any) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        yield "agent.completed", {"agent": "analyze_situation"}
        yield "retrieval.completed", {"retrieval_id": "ret_test", "citation_count": 1}
        yield "result", answer_data()


def test_answer_and_stream_contracts() -> None:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_agent_workflow] = lambda: FakeAgent()
    with TestClient(app) as client:
        response = client.post("/v1/answers", json={"question": "Lan chiem dat co bi cam?"})
        assert response.status_code == 200
        assert response.json()["claims"][0]["citation_ids"] == ["cit_01"]

        streamed = client.post("/v1/answers:stream", json={"question": "Lan chiem dat co bi cam?"})
        assert streamed.status_code == 200
        assert streamed.headers["content-type"].startswith("text/event-stream")
        events = streamed.text
        assert events.index("event: retrieval.completed") < events.index("event: citation")
        assert events.index("event: citation") < events.index("event: answer.delta")
        assert "event: answer.completed" in events
