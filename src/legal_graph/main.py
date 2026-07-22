from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from legal_graph.agents import LegalAgentWorkflow
from legal_graph.application.services import RetrievalService
from legal_graph.core.config import ROOT, Settings, get_settings
from legal_graph.core.errors import AppError
from legal_graph.core.middleware import RequestContextMiddleware
from legal_graph.http.v1.router import router
from legal_graph.infrastructure.neo4j_repository import Neo4jLegalGraphRepository
from legal_graph.infrastructure.openai_chat import OpenAIChatProvider
from legal_graph.infrastructure.openai_embeddings import OpenAIEmbeddingProvider


def error_body(
    request: Request, code: str, message: str, details: list[dict[str, Any]], retryable: bool
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "retryable": retryable,
        }
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        repository = Neo4jLegalGraphRepository.create(
            settings.neo4j_uri,
            settings.neo4j_credentials,
            settings.neo4j_database,
            settings.openai_embedding_dimensions,
        )
        embeddings = OpenAIEmbeddingProvider(
            settings.openai_api_key.get_secret_value(),
            settings.openai_embedding_model,
            settings.openai_embedding_dimensions,
            settings.request_timeout_ms / 1000,
        )
        chat = OpenAIChatProvider(
            settings.openai_api_key.get_secret_value(), settings.answer_timeout_ms / 1000
        )
        checkpoint_path = Path(settings.agent_checkpoint_path)
        if not checkpoint_path.is_absolute():
            checkpoint_path = ROOT / checkpoint_path
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as checkpointer:
            await checkpointer.setup()
            retrieval_service = RetrievalService(repository, embeddings)
            app.state.repository = repository
            app.state.embeddings = embeddings
            app.state.chat = chat
            app.state.retrieval_service = retrieval_service
            app.state.agent_workflow = LegalAgentWorkflow(
                retrieval_service, chat, settings, checkpointer
            )
            await repository.ensure_indexes()
            try:
                yield
            finally:
                await chat.close()
                await embeddings.close()
                await repository.close()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
        headers = {"Retry-After": "5"} if error.retryable else None
        return JSONResponse(
            error_body(request, error.code, error.message, error.details, error.retryable),
            status_code=error.status_code,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        details = [
            {"field": ".".join(str(part) for part in item["loc"]), "reason": item["msg"]}
            for item in error.errors()
        ]
        return JSONResponse(
            error_body(request, "INVALID_REQUEST", "Request validation failed", details, False),
            status_code=400,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(
            error_body(
                request,
                "INTERNAL_ERROR",
                "An unexpected internal error occurred",
                [],
                False,
            ),
            status_code=500,
        )

    return app


app = create_app()


def run() -> None:
    uvicorn.run("legal_graph.main:app", host="0.0.0.0", port=8000, reload=False)
