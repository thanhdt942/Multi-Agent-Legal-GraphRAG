#!/usr/bin/env python3
"""Rebuild Neo4j entirely from local artifacts without calling OpenAI."""

import argparse
import subprocess
import sys
from pathlib import Path

from neo4j_client import get_driver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete all current Neo4j nodes before importing artifacts.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    required = [
        root / "artifacts" / "flatten.jsonl",
        root / "artifacts" / "relationship.parquet",
        root / "artifacts" / "extracted_relations.jsonl",
        root / "artifacts" / "extracted_behaviors.jsonl",
        root / "artifacts" / "legal_node_embeddings.parquet",
        root / "artifacts" / "article_comparison_embeddings.parquet",
        root / "artifacts" / "behavior_embeddings.parquet",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required artifacts: {missing}")

    if args.clear:
        driver = get_driver()
        try:
            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n").consume()
            print("[rebuild] Cleared current Neo4j graph")
        finally:
            driver.close()

    print("[rebuild] Importing structural nodes and source relationships")
    subprocess.run(
        [sys.executable, str(root / "scripts" / "import_neo4j.py")],
        cwd=root,
        check=True,
    )
    print("[rebuild] Importing semantic artifacts and cached embeddings")
    subprocess.run(
        [sys.executable, str(root / "scripts" / "import_artifacts.py")],
        cwd=root,
        check=True,
    )
    print("[rebuild] Completed without OpenAI API calls")


if __name__ == "__main__":
    main()
