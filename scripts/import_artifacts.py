#!/usr/bin/env python3
"""Import extracted relations, behaviors, and cached vectors into Neo4j."""

import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from neo4j_client import get_credentials, get_driver


IMPORT_STATUSES = {"VERIFIED", "PROPOSED"}
RELATION_TYPES = {
    "THAY_THE",
    "SUA_DOI",
    "TUONG_UNG",
    "DAN_CHIEU",
    "AP_DUNG_CHUYEN_TIEP",
    "LAM_HET_HIEU_LUC",
}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def neo4j_value(value):
    if isinstance(value, (dict, tuple)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list) and not all(
        isinstance(item, (str, int, float, bool)) or item is None for item in value
    ):
        return json.dumps(value, ensure_ascii=False)
    return value


def clean_properties(record: dict, excluded: set[str]) -> dict:
    return {
        key: neo4j_value(value)
        for key, value in record.items()
        if key not in excluded and value is not None
    }


def create_constraints(driver):
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT behavior_id IF NOT EXISTS "
            "FOR (n:HanhVi) REQUIRE n.id IS UNIQUE"
        )


def clear_previous_artifact_import(driver):
    """Remove only generated semantic data, preserving base graph relations."""
    with driver.session() as session:
        session.run(
            """
            MATCH ()-[r]->()
            WHERE r.method IN ['RULE', 'LLM']
            DELETE r
            """
        ).consume()
        session.run("MATCH (h:HanhVi) DETACH DELETE h").consume()


def import_behaviors(driver, records: list[dict]):
    rows = []
    for record in records:
        if record.get("status") not in IMPORT_STATUSES:
            continue
        rows.append(
            {
                "id": record["id"],
                "source_node_id": record["source_node_id"],
                "properties": clean_properties(
                    record, {"id", "source_node_id"}
                ),
            }
        )
    if not rows:
        return 0
    with driver.session() as session:
        session.run(
            """
            UNWIND $rows AS row
            MERGE (h:HanhVi:SemanticNode {id: row.id})
            SET h += row.properties
            WITH h, row
            MATCH (source:LegalNode {id: row.source_node_id})
            MERGE (h)-[r:VI_PHAM]->(source)
            SET r.status = h.status,
                r.confidence = h.confidence,
                r.method = h.method,
                r.model = h.model,
                r.evidence = h.evidence
            """,
            rows=rows,
        ).consume()
    return len(rows)


def import_relations(driver, records: list[dict]):
    grouped = defaultdict(list)
    for record in records:
        rel_type = record.get("relationship")
        if record.get("status") not in IMPORT_STATUSES or rel_type not in RELATION_TYPES:
            continue
        grouped[rel_type].append(
            {
                "source_id": record["source_id"],
                "target_id": record["target_id"],
                "properties": clean_properties(
                    record, {"source_id", "target_id", "relationship"}
                ),
            }
        )

    imported = 0
    for rel_type, rows in grouped.items():
        with driver.session() as session:
            session.run(
                f"""
                UNWIND $rows AS row
                MATCH (source:LegalNode {{id: row.source_id}})
                MATCH (target:LegalNode {{id: row.target_id}})
                MERGE (source)-[r:{rel_type}]->(target)
                SET r += row.properties
                """,
                rows=rows,
            ).consume()
        imported += len(rows)
    return imported


def import_vector_parquet(
    driver,
    path: Path,
    vector_field: str,
    hash_field: str,
    batch_size: int = 200,
):
    if not path.exists():
        return 0
    frame = pd.read_parquet(path)
    rows = []
    for record in frame.to_dict(orient="records"):
        vector = record[vector_field]
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        rows.append(
            {
                "node_id": record["node_id"],
                "vector": vector,
                "text_hash": record[hash_field],
                "model": record["model"],
                "dimensions": int(record["dimensions"]),
            }
        )

    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        with driver.session() as session:
            session.run(
                f"""
                UNWIND $rows AS row
                MATCH (n {{id: row.node_id}})
                SET n.{vector_field} = row.vector,
                    n.{hash_field} = row.text_hash,
                    n.{vector_field}_model = row.model,
                    n.{vector_field}_dimensions = row.dimensions
                """,
                rows=batch,
            ).consume()
    return len(rows)


def create_vector_indexes(driver, dimensions: int = 1536):
    specs = [
        ("legal_node_embedding", "LegalNode", "embedding"),
        ("article_comparison_embedding", "Article", "comparison_embedding"),
        ("behavior_embedding", "HanhVi", "embedding"),
    ]
    with driver.session() as session:
        existing = {
            record["name"]: dict(record)
            for record in session.run(
                "SHOW VECTOR INDEXES YIELD name, labelsOrTypes, properties "
                "RETURN name, labelsOrTypes, properties"
            )
        }
        for name, label, property_name in specs:
            current = existing.get(name)
            if current and (
                current["labelsOrTypes"] != [label]
                or current["properties"] != [property_name]
            ):
                session.run(f"DROP INDEX {name} IF EXISTS").consume()
                current = None
            if not current:
                session.run(
                    f"""
                    CREATE VECTOR INDEX {name} IF NOT EXISTS
                    FOR (n:{label}) ON n.{property_name}
                    OPTIONS {{indexConfig: {{`vector.dimensions`: {dimensions},
                             `vector.similarity_function`: 'cosine'}}}}
                    """
                ).consume()


def cypher_literal(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(neo4j_value(value), ensure_ascii=False)


def cypher_map(record: dict) -> str:
    return "{" + ", ".join(
        f"{key}: {cypher_literal(value)}" for key, value in record.items()
    ) + "}"


def generate_cypher(path: Path, relations: list[dict], behaviors: list[dict]):
    lines = [
        "// Generated semantic nodes and relations. Embeddings are imported from Parquet.",
        "CREATE CONSTRAINT behavior_id IF NOT EXISTS FOR (n:HanhVi) REQUIRE n.id IS UNIQUE;",
        "",
    ]
    accepted_behaviors = [
        record for record in behaviors if record.get("status") in IMPORT_STATUSES
    ]
    if accepted_behaviors:
        rows = []
        for record in accepted_behaviors:
            rows.append(
                {
                    "id": record["id"],
                    "source_node_id": record["source_node_id"],
                    "properties": json.dumps(
                        clean_properties(record, {"id", "source_node_id"}),
                        ensure_ascii=False,
                    ),
                }
            )
        for row in rows:
            lines.extend(
                [
                    f"MERGE (h:HanhVi:SemanticNode {{id: {cypher_literal(row['id'])}}})",
                    f"SET h += apoc.convert.fromJsonMap({cypher_literal(row['properties'])})",
                    f"WITH h MATCH (source:LegalNode {{id: {cypher_literal(row['source_node_id'])}}})",
                    "MERGE (h)-[r:VI_PHAM]->(source)",
                    "SET r.status = h.status, r.confidence = h.confidence, "
                    "r.method = h.method, r.model = h.model, r.evidence = h.evidence;",
                    "",
                ]
            )

    for record in relations:
        rel_type = record.get("relationship")
        if record.get("status") not in IMPORT_STATUSES or rel_type not in RELATION_TYPES:
            continue
        properties = json.dumps(
            clean_properties(record, {"source_id", "target_id", "relationship"}),
            ensure_ascii=False,
        )
        lines.extend(
            [
                f"MATCH (source:LegalNode {{id: {cypher_literal(record['source_id'])}}})",
                f"MATCH (target:LegalNode {{id: {cypher_literal(record['target_id'])}}})",
                f"MERGE (source)-[r:{rel_type}]->(target)",
                f"SET r += apoc.convert.fromJsonMap({cypher_literal(properties)});",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(artifacts: Path, relations: list[dict], behaviors: list[dict]):
    root = artifacts.parent
    parsed_path = artifacts / "parsed.json"
    if not parsed_path.exists():
        parsed_path = root / "parsed.json"
    relationship_path = artifacts / "relationship.parquet"
    if not relationship_path.exists():
        relationship_path = root / "relationship.parquet"
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_documents": ["32833", "177815"],
        "embedding_model": os.environ.get(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        ),
        "embedding_dimensions": int(
            os.environ.get("OPENAI_EMBEDDING_DIMENSIONS", "1536")
        ),
        "extraction_model": os.environ.get("OPENAI_EXTRACTION_MODEL", "gpt-5-nano"),
        "hashes": {
            "parsed.json": sha256_file(parsed_path),
            "relationship.parquet": sha256_file(relationship_path),
            "flatten.jsonl": sha256_file(artifacts / "flatten.jsonl"),
        },
        "counts": {
            "relations_total": len(relations),
            "relations_importable": sum(
                record.get("status") in IMPORT_STATUSES for record in relations
            ),
            "behaviors_total": len(behaviors),
            "behaviors_importable": sum(
                record.get("status") in IMPORT_STATUSES for record in behaviors
            ),
        },
    }
    (artifacts / "extraction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def verify(driver):
    with driver.session() as session:
        counts = session.run(
            """
            MATCH (h:HanhVi) WITH count(h) AS behaviors
            MATCH ()-[r]->()
            WHERE type(r) IN ['THAY_THE', 'SUA_DOI', 'TUONG_UNG', 'DAN_CHIEU',
                              'AP_DUNG_CHUYEN_TIEP', 'LAM_HET_HIEU_LUC', 'VI_PHAM']
            RETURN behaviors, type(r) AS relationship, count(r) AS count
            ORDER BY relationship
            """
        )
        rows = [dict(record) for record in counts]
        invalid = session.run(
            """
            MATCH (source:Article)-[r:THAY_THE|SUA_DOI|TUONG_UNG|DAN_CHIEU]->(target:Article)
            WHERE source.document_id <> '177815' OR target.document_id <> '32833'
            RETURN count(r) AS count
            """
        ).single()["count"]
    print(f"[verify] semantic graph counts={rows}")
    print(f"[verify] out-of-scope Article relations={invalid}")


def main():
    root = Path(__file__).resolve().parent.parent
    artifacts = root / "artifacts"
    relations = load_jsonl(artifacts / "extracted_relations.jsonl")
    behaviors = load_jsonl(artifacts / "extracted_behaviors.jsonl")

    embedding_model = os.environ.get(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    extraction_model = os.environ.get("OPENAI_EXTRACTION_MODEL", "gpt-5-nano")
    dimensions = int(os.environ.get("OPENAI_EMBEDDING_DIMENSIONS", "1536"))
    print(f"[model] Embedding model: {embedding_model} ({dimensions} dimensions)")
    print(f"[model] Relation/behavior extraction model: {extraction_model}")
    uri, user = get_credentials()
    print(f"[config] Neo4j: {uri} as {user}")

    driver = get_driver()
    try:
        create_constraints(driver)
        clear_previous_artifact_import(driver)
        behavior_count = import_behaviors(driver, behaviors)
        relation_count = import_relations(driver, relations)
        embedding_count = import_vector_parquet(
            driver,
            artifacts / "legal_node_embeddings.parquet",
            "embedding",
            "embedding_text_hash",
        )
        comparison_count = import_vector_parquet(
            driver,
            artifacts / "article_comparison_embeddings.parquet",
            "comparison_embedding",
            "comparison_text_hash",
        )
        behavior_embedding_count = import_vector_parquet(
            driver,
            artifacts / "behavior_embeddings.parquet",
            "embedding",
            "embedding_text_hash",
        )
        create_vector_indexes(driver, dimensions)
        print(
            f"[import] behaviors={behavior_count}, relations={relation_count}, "
            f"embeddings={embedding_count}, comparison_embeddings={comparison_count}, "
            f"behavior_embeddings={behavior_embedding_count}"
        )
        verify(driver)
    finally:
        driver.close()

    generate_cypher(
        artifacts / "import_extracted_relations.cypher", relations, behaviors
    )
    write_manifest(artifacts, relations, behaviors)
    print("[save] Generated import_extracted_relations.cypher and extraction_manifest.json")


if __name__ == "__main__":
    main()
