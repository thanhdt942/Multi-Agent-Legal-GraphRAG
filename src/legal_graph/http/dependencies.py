from fastapi import Request

from legal_graph.agents import LegalAgentWorkflow
from legal_graph.application.services import RetrievalService
from legal_graph.infrastructure.neo4j_repository import Neo4jLegalGraphRepository


def get_repository(request: Request) -> Neo4jLegalGraphRepository:
    return request.app.state.repository


def get_service(request: Request) -> RetrievalService:
    return request.app.state.retrieval_service


def get_agent_workflow(request: Request) -> LegalAgentWorkflow:
    return request.app.state.agent_workflow
