#!/usr/bin/env python3
"""Embed LegalNode.embedding_text and Article.comparison_text into Neo4j.

Models and settings are read from .env:
    OPENAI_EMBEDDING_MODEL (default: text-embedding-3-small)
    OPENAI_EMBEDDING_DIMENSIONS (default: 1536)

Output artifacts:
    artifacts/legal_node_embeddings.parquet
    artifacts/article_comparison_embeddings.parquet
"""

import hashlib
import os
import time
from pathlib import Path

import pandas as pd
import tiktoken
from openai import OpenAI, RateLimitError

from neo4j_client import get_credentials, get_driver


def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=api_key)


def get_model_config():
    model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    dimensions = int(os.environ.get("OPENAI_EMBEDDING_DIMENSIONS", "1536"))
    return model, dimensions


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def truncate_text(text: str, tokenizer, max_tokens: int) -> str:
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return text
    truncated = tokenizer.decode(tokens[:max_tokens])
    return truncated


def fetch_nodes_needing_embedding(driver, label: str, text_field: str, vector_field: str):
    """Return nodes whose stored vector is missing or stale."""
    query = f"""
        MATCH (n:{label})
        WHERE n.{text_field} IS NOT NULL
        RETURN n.id AS id, n.{text_field} AS text,
               n.{vector_field} AS vector, n.{text_field}_hash AS stored_hash
    """
    with driver.session() as session:
        result = session.run(query)
        rows = [dict(record) for record in result]

    needed = []
    for row in rows:
        current_hash = hash_text(row["text"])
        if row["vector"] is None or row["stored_hash"] != current_hash:
            needed.append({
                "id": row["id"],
                "text": row["text"],
                "text_hash": current_hash,
            })
    return needed


def embed_batch(client, texts: list[str], model: str, dimensions: int, max_retries: int = 5):
    """Call OpenAI embeddings API with retries."""
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=texts,
                model=model,
                dimensions=dimensions,
            )
            return [item.embedding for item in response.data]
        except RateLimitError as e:
            wait = 2 ** attempt
            print(f"[embed] Rate limited, retrying in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"[embed] Error: {e}, retrying...")
            time.sleep(1)
    raise RuntimeError("Failed to embed batch after retries")


def save_embeddings_to_neo4j(
    driver,
    label: str,
    nodes: list[dict],
    vector_field: str,
    hash_field: str,
    model: str,
    dimensions: int,
    batch_size: int = 500,
):
    """Write vectors back to Neo4j."""
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i : i + batch_size]
        with driver.session() as session:
            session.run(
                f"""
                UNWIND $batch AS row
                MATCH (n:{label} {{id: row.id}})
                SET n.{vector_field} = row.vector,
                    n.{hash_field} = row.text_hash,
                    n.{vector_field}_model = $model,
                    n.{vector_field}_dimensions = $dimensions,
                    n.{vector_field}_at = datetime()
                """,
                batch=batch,
                model=model,
                dimensions=dimensions,
            )


def save_embeddings_to_parquet(nodes: list[dict], vector_field: str, text_field: str, model: str, dimensions: int, parquet_path: Path):
    """Persist vectors to Parquet for offline re-import."""
    if not nodes:
        return
    df = pd.DataFrame([
        {
            "node_id": n["id"],
            f"{text_field}_hash": n["text_hash"],
            "model": model,
            "dimensions": dimensions,
            vector_field: n["vector"],
        }
        for n in nodes
    ])
    if parquet_path.exists():
        existing = pd.read_parquet(parquet_path)
        df = pd.concat([existing, df], ignore_index=True)
        df = df.drop_duplicates(subset=["node_id"], keep="last")
    df.to_parquet(parquet_path, index=False)
    print(f"[embed] Wrote {len(df)} cached vectors to {parquet_path}")


def create_vector_index(driver, index_name: str, label: str, vector_field: str, dimensions: int):
    """Create a cosine vector index if it does not exist."""
    query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (n:{label})
        ON n.{vector_field}
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimensions},
                `vector.similarity_function`: 'cosine'
            }}
        }}
    """
    with driver.session() as session:
        current = session.run(
            "SHOW VECTOR INDEXES YIELD name, labelsOrTypes, properties "
            "WHERE name = $name RETURN labelsOrTypes, properties",
            name=index_name,
        ).single()
        if current and (
            current["labelsOrTypes"] != [label]
            or current["properties"] != [vector_field]
        ):
            session.run(f"DROP INDEX {index_name} IF EXISTS").consume()
        session.run(query)
    print(f"[embed] Created/verified vector index '{index_name}'")


def embed_nodes(driver, label: str, text_field: str, vector_field: str, parquet_path: Path, model: str, dimensions: int, max_tokens: int = 8000, max_batch_tokens: int = 250000):
    """Embed a group of nodes and persist results.

    Batches are built dynamically so that the total tokens per OpenAI request
    stays below max_batch_tokens.
    """
    client = get_openai_client()
    tokenizer = tiktoken.encoding_for_model(model)

    needed = fetch_nodes_needing_embedding(driver, label, text_field, vector_field)
    print(f"[embed] {len(needed)} {label} nodes need {vector_field}")
    if not needed:
        return []

    # Truncate texts.
    for node in needed:
        node["text"] = truncate_text(node["text"], tokenizer, max_tokens)
        node["token_count"] = len(tokenizer.encode(node["text"]))

    # Embed in token-bounded batches.
    embedded_nodes = []
    total_tokens = 0
    batch = []
    batch_tokens = 0
    for node in needed:
        if batch and batch_tokens + node["token_count"] > max_batch_tokens:
            texts = [n["text"] for n in batch]
            total_tokens += batch_tokens
            vectors = embed_batch(client, texts, model, dimensions)
            for n, vector in zip(batch, vectors):
                n["vector"] = vector
                embedded_nodes.append(n)
            print(f"[embed] Embedded {len(embedded_nodes)}/{len(needed)} {label} nodes")
            batch = []
            batch_tokens = 0
        batch.append(node)
        batch_tokens += node["token_count"]

    if batch:
        texts = [n["text"] for n in batch]
        total_tokens += batch_tokens
        vectors = embed_batch(client, texts, model, dimensions)
        for n, vector in zip(batch, vectors):
            n["vector"] = vector
            embedded_nodes.append(n)
        print(f"[embed] Embedded {len(embedded_nodes)}/{len(needed)} {label} nodes")

    # Persist.
    save_embeddings_to_neo4j(
        driver,
        label,
        embedded_nodes,
        vector_field,
        f"{text_field}_hash",
        model,
        dimensions,
    )
    save_embeddings_to_parquet(embedded_nodes, vector_field, text_field, model, dimensions, parquet_path)

    print(f"[embed] {vector_field} total tokens sent: {total_tokens}")
    return embedded_nodes


def main():
    model, dimensions = get_model_config()
    uri, user = get_credentials()
    print(f"[config] Neo4j: {uri} as {user}")
    print(f"[model] Embedding model: {model}")
    print(f"[model] Embedding dimensions: {dimensions}")

    root = Path(__file__).resolve().parent.parent
    artifacts_dir = root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    driver = get_driver()
    try:
        # 1. Embed all LegalNode.embedding_text
        embed_nodes(
            driver,
            label="LegalNode",
            text_field="embedding_text",
            vector_field="embedding",
            parquet_path=artifacts_dir / "legal_node_embeddings.parquet",
            model=model,
            dimensions=dimensions,
        )

        # 2. Embed Article.comparison_text
        embed_nodes(
            driver,
            label="Article",
            text_field="comparison_text",
            vector_field="comparison_embedding",
            parquet_path=artifacts_dir / "article_comparison_embeddings.parquet",
            model=model,
            dimensions=dimensions,
        )

        # 3. Embed extracted behavior nodes.
        embed_nodes(
            driver,
            label="HanhVi",
            text_field="embedding_text",
            vector_field="embedding",
            parquet_path=artifacts_dir / "behavior_embeddings.parquet",
            model=model,
            dimensions=dimensions,
        )

        # 4. Create vector indexes.
        create_vector_index(
            driver, "legal_node_embedding", "LegalNode", "embedding", dimensions
        )
        create_vector_index(
            driver,
            "article_comparison_embedding",
            "Article",
            "comparison_embedding",
            dimensions,
        )
        create_vector_index(
            driver, "behavior_embedding", "HanhVi", "embedding", dimensions
        )

        # 5. Verify.
        with driver.session() as session:
            result = session.run("""
                MATCH (n:LegalNode)
                RETURN count(n) AS total,
                       count(n.embedding) AS embedded,
                       count(n.comparison_embedding) AS comparison_embedded
            """)
            record = result.single()
            print("\n[verify] Embedding counts:")
            print(f"  Total nodes: {record['total']}")
            print(f"  With embedding: {record['embedded']}")
            print(f"  With comparison_embedding: {record['comparison_embedded']}")
            behavior = session.run("""
                MATCH (h:HanhVi)
                RETURN count(h) AS total, count(h.embedding) AS embedded
            """).single()
            print(f"  Behavior nodes: {behavior['total']}")
            print(f"  Behaviors with embedding: {behavior['embedded']}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
