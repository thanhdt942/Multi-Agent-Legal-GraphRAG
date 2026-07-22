"""Shared Neo4j connection helper."""

import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")


def get_driver():
    """Create a Neo4j driver from environment variables."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    auth = os.environ.get("NEO4J_AUTH", "neo4j/legaldoc123")
    user, password = auth.split("/", 1)
    return GraphDatabase.driver(uri, auth=(user, password))


def get_credentials():
    """Return Neo4j connection info for display."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    auth = os.environ.get("NEO4J_AUTH", "neo4j/legaldoc123")
    user, _ = auth.split("/", 1)
    return uri, user
