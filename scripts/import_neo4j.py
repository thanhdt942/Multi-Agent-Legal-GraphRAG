#!/usr/bin/env python3
"""Import flatten.jsonl and relationship.parquet into Neo4j using Python driver.

Usage:
    python scripts/import_neo4j.py

Environment variables:
    NEO4J_URI     default: bolt://localhost:7687
    NEO4J_USER    default: neo4j
    NEO4J_PASS    default: legaldoc123
"""

import json
import os
from collections import defaultdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Support both the development layout and the two-folder migration bundle.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

from rel_normalizer import normalize_relationship


def load_nodes(flatten_path: Path) -> list[dict]:
    nodes = []
    with open(flatten_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            nodes.append(json.loads(line))
    return nodes


def create_constraints(tx):
    tx.run("""
        CREATE CONSTRAINT legal_node_id IF NOT EXISTS
        FOR (n:LegalNode)
        REQUIRE n.id IS UNIQUE
    """)
    tx.run("""
        CREATE CONSTRAINT legal_document_id IF NOT EXISTS
        FOR (n:Document)
        REQUIRE n.document_id IS UNIQUE
    """)


def import_nodes(driver, nodes: list[dict], batch_size: int = 500):
    # Group by level to use static labels in Cypher.
    by_level = defaultdict(list)
    for node in nodes:
        label = node["level"].capitalize()
        by_level[label].append(node)

    for label, level_nodes in by_level.items():
        print(f"[import] Importing {len(level_nodes)} {label} nodes...")
        for i in range(0, len(level_nodes), batch_size):
            batch = level_nodes[i : i + batch_size]
            props_batch = []
            for node in batch:
                props = dict(node)
                props_batch.append(props)

            with driver.session() as session:
                session.run(
                    f"""
                    UNWIND $batch AS row
                    MERGE (n:{label}:LegalNode {{id: row.id}})
                    SET n += row
                    """,
                    batch=props_batch,
                )


def import_hierarchy(driver, nodes: list[dict], batch_size: int = 1000):
    rels = [
        {"child_id": n["id"], "parent_id": n["parent_key"]}
        for n in nodes
        if n.get("parent_key") is not None
    ]
    if not rels:
        return
    print(f"[import] Importing {len(rels)} hierarchy relationships...")
    for i in range(0, len(rels), batch_size):
        batch = rels[i : i + batch_size]
        with driver.session() as session:
            session.run(
                """
                UNWIND $batch AS row
                MATCH (child:LegalNode {id: row.child_id})
                MATCH (parent:LegalNode {id: row.parent_id})
                MERGE (parent)-[:HAS_CHILD]->(child)
                """,
                batch=batch,
            )


def import_document_relationships(driver, rel_path: Path):
    df = pd.read_parquet(rel_path)
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "doc_id": str(row["doc_id"]),
                "other_doc_id": str(row["other_doc_id"]),
                "rel_type": normalize_relationship(str(row["relationship"])),
            }
        )
    if not rows:
        return
    print(f"[import] Importing {len(rows)} document relationships...")
    for item in rows:
        rel_type = item["rel_type"]
        with driver.session() as session:
            session.run(
                f"""
                MATCH (d1:Document {{document_id: $doc_id}})
                MATCH (d2:Document {{document_id: $other_doc_id}})
                MERGE (d1)-[:{rel_type}]->(d2)
                """,
                doc_id=item["doc_id"],
                other_doc_id=item["other_doc_id"],
            )


def verify(driver):
    with driver.session() as session:
        result = session.run("""
            MATCH (n:LegalNode)
            RETURN labels(n)[0] AS label, count(*) AS cnt
            ORDER BY cnt DESC
        """)
        print("\n[verify] Node counts by label:")
        for record in result:
            print(f"  {record['label']}: {record['cnt']}")

        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS rel_type, count(*) AS cnt
            ORDER BY cnt DESC
        """)
        print("\n[verify] Relationship counts:")
        for record in result:
            print(f"  {record['rel_type']}: {record['cnt']}")


def main():
    root = Path(__file__).resolve().parent.parent
    artifacts_dir = root / "artifacts"
    flatten_path = artifacts_dir / "flatten.jsonl"
    rel_path = artifacts_dir / "relationship.parquet"
    if not rel_path.exists():
        rel_path = root / "relationship.parquet"

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    auth = os.environ.get("NEO4J_AUTH", "neo4j/legaldoc123")
    user, password = auth.split("/", 1)

    print(f"[config] Connecting to {uri} as {user}")
    nodes = load_nodes(flatten_path)
    print(f"[load] Loaded {len(nodes)} nodes from {flatten_path}")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            session.execute_write(create_constraints)
        print("[import] Constraints created/verified")

        import_nodes(driver, nodes)
        import_hierarchy(driver, nodes)
        import_document_relationships(driver, rel_path)
        verify(driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
