#!/usr/bin/env python3
"""Prepare artifacts/ as the self-contained data folder for migration."""

import hashlib
import json
import shutil
from pathlib import Path


REQUIRED_ARTIFACTS = (
    "flatten.jsonl",
    "extracted_relations.jsonl",
    "extracted_behaviors.jsonl",
    "legal_node_embeddings.parquet",
    "article_comparison_embeddings.parquet",
    "behavior_embeddings.parquet",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    root = Path(__file__).resolve().parent.parent
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    missing = [name for name in REQUIRED_ARTIFACTS if not (artifacts / name).exists()]
    if missing:
        raise SystemExit(f"Missing required artifacts: {missing}")

    source_files = ("relationship.parquet", "parsed.json")
    for name in source_files:
        source = root / name
        target = artifacts / name
        if not source.exists() and not target.exists():
            raise SystemExit(f"Missing source data: {source}")
        if source.exists() and source.resolve() != target.resolve():
            shutil.copy2(source, target)
            print(f"[copy] {source} -> {target}")

    tracked_files = [*REQUIRED_ARTIFACTS, *source_files]
    manifest = {
        "bundle_version": 1,
        "data_directory": "artifacts",
        "files": {
            name: {
                "size_bytes": (artifacts / name).stat().st_size,
                "sha256": sha256_file(artifacts / name),
            }
            for name in tracked_files
        },
    }
    manifest_path = artifacts / "migration_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[save] {manifest_path}")
    print("[ready] Copy only artifacts/ and scripts/ to the target project")


if __name__ == "__main__":
    main()
