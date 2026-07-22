#!/usr/bin/env python3
"""Build artifacts/flatten.jsonl and artifacts/import.cypher from parsed.json.

Output:
  - artifacts/flatten.jsonl: one JSON object per node, with document_id,
    parent_key, level, all original fields, embedding_text (title + ancestor
    context) and comparison_text (full article subtree) for Articles.
  - artifacts/import.cypher: standalone Cypher script to import the same data
    into Neo4j (constraints, nodes, hierarchy, document relationships).
"""

import json
from pathlib import Path
from typing import Any

from rel_normalizer import normalize_relationship


# Child mapping for the parsed hierarchy.
CHILD_MAP = {
    "document": ["chapters"],
    "chapter": ["sections", "articles"],
    "section": ["articles"],
    "article": ["clauses"],
    "clause": ["points"],
}


def build_context(node: dict, level: str) -> str:
    """Build a short human-readable context string for a node."""
    number = (node.get("number") or "").strip()
    title = (node.get("title") or "").strip()
    content = (node.get("content") or "").strip()

    if level == "document":
        doc_type = (node.get("document_type") or "").strip()
        doc_num = (node.get("document_number") or "").strip()
        doc_name = (node.get("document_name") or "").strip()
        header = f"{doc_type} số {doc_num}".strip()
        if doc_name:
            header = f"{header} {doc_name}".strip()
        parts = [header]
        if content:
            parts.append(content)
    elif level == "chapter":
        header = f"Chương {number}".strip()
        if title:
            header = f"{header}. {title}".strip()
        parts = [header]
    elif level == "section":
        header = f"Mục {number}".strip()
        if title:
            header = f"{header}. {title}".strip()
        parts = [header]
    elif level == "article":
        header = f"Điều {number}".strip()
        if title:
            header = f"{header}. {title}".strip()
        parts = [header]
        if content:
            parts.append(content)
    elif level == "clause":
        header = f"Khoản {number}".strip()
        parts = [header]
        if content:
            parts.append(content)
    elif level == "point":
        header = f"Điểm {number}".strip()
        parts = [header]
        if content:
            parts.append(content)
    else:
        parts = []

    return " ".join(p.strip() for p in parts if p.strip())


def make_embedding_text(node: dict, ancestors: list[dict]) -> str:
    """Combine ancestor contexts with the node's own context."""
    parts = [build_context(anc, anc["level"]) for anc in ancestors]
    parts.append(build_context(node, node["level"]))
    parts = [p for p in parts if p.strip()]
    return " | ".join(parts)


def flatten_node(node: dict, parent_key: str | None, ancestors: list[dict]) -> dict:
    """Convert a parsed node into a flat record ready for Neo4j."""
    level = node["level"]
    flat = {
        "id": node["id"],
        "document_id": node["document_id"],
        "parent_key": parent_key,
        "level": level,
    }

    # Copy all original scalar fields except nested children.
    children_keys = {"chapters", "sections", "articles", "clauses", "points"}
    for key, value in node.items():
        if key in children_keys:
            continue
        flat[key] = value

    # Flatten the nested `source` dict into top-level properties.
    if "source" in flat and isinstance(flat["source"], dict):
        source = flat.pop("source")
        for sk, sv in source.items():
            flat[sk] = sv

    flat["embedding_text"] = make_embedding_text(node, ancestors)
    return flat


def walk_tree(node: dict, parent_key: str | None, ancestors: list[dict], output: list):
    flat = flatten_node(node, parent_key, ancestors)
    output.append(flat)

    new_ancestors = ancestors + [node]
    level = node["level"]
    for child_key in CHILD_MAP.get(level, []):
        for child in node.get(child_key, []):
            walk_tree(child, node["id"], new_ancestors, output)


def build_subtree_text(node: dict, children_by_id: dict, indent: int = 0) -> str:
    """Recursively build a readable text representation of a node and its children."""
    level = node["level"]
    number = (node.get("number") or "").strip()
    title = (node.get("title") or "").strip()
    content = (node.get("content") or "").strip()

    prefix = "  " * indent
    if level == "article":
        line = f"{prefix}Điều {number}"
        if title:
            line = f"{line}. {title}"
    elif level == "clause":
        line = f"{prefix}Khoản {number}"
    elif level == "point":
        line = f"{prefix}Điểm {number}"
    else:
        line = ""

    parts = [line] if line else []
    if content:
        parts.append(f"{prefix}{content}")

    for child in children_by_id.get(node["id"], []):
        parts.append(build_subtree_text(child, children_by_id, indent + 1))

    return "\n".join(p for p in parts if p)


def build_article_comparison_text(node: dict, ancestors: list[dict], children_by_id: dict) -> str:
    """Build a full article text including its ancestor context and subtree.

    Unlike embedding_text, this includes the full article subtree (clauses/points)
    but keeps the ancestor header short (document name only, not full content).
    """
    header_parts = []
    for anc in ancestors:
        if anc["level"] == "document":
            doc_type = (anc.get("document_type") or "").strip()
            doc_num = (anc.get("document_number") or "").strip()
            doc_name = (anc.get("document_name") or "").strip()
            header = f"{doc_type} số {doc_num}".strip()
            if doc_name:
                header = f"{header} {doc_name}".strip()
            header_parts.append(header)
        elif anc["level"] in {"chapter", "section"}:
            header_parts.append(build_context(anc, anc["level"]))

    subtree = build_subtree_text(node, children_by_id, indent=0)

    lines = []
    if header_parts:
        lines.append("\n".join(header_parts))
    lines.append(subtree)
    return "\n".join(lines)


def build_flatten(parsed_path: Path, output_path: Path) -> list[dict]:
    with open(parsed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = data.get("documents", [])
    nodes = []
    for doc in documents:
        walk_tree(doc, None, [], nodes)

    # Build parent -> children map for comparison_text generation.
    children_by_id: dict[str, list[dict]] = {}
    for n in nodes:
        pk = n.get("parent_key")
        if pk:
            children_by_id.setdefault(pk, []).append(n)

    # Add comparison_text for Articles.
    # We need the original parsed nodes, so walk the tree again while keeping ancestors.
    for doc in documents:
        _add_comparison_text(doc, [], children_by_id, nodes_by_id={n["id"]: n for n in nodes})

    with open(output_path, "w", encoding="utf-8") as f:
        for node in nodes:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")

    print(f"[flatten] Wrote {len(nodes)} nodes to {output_path}")
    return nodes


def _add_comparison_text(node: dict, ancestors: list[dict], children_by_id: dict, nodes_by_id: dict):
    """Recursively add comparison_text to Article nodes."""
    if node["level"] == "article":
        flat_node = nodes_by_id[node["id"]]
        flat_node["comparison_text"] = build_article_comparison_text(
            node, ancestors, children_by_id
        )

    new_ancestors = ancestors + [node]
    level = node["level"]
    for child_key in CHILD_MAP.get(level, []):
        for child in node.get(child_key, []):
            _add_comparison_text(child, new_ancestors, children_by_id, nodes_by_id)


def to_cypher_literal(value: Any) -> str:
    """Convert a Python value to a Cypher literal string."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise TypeError(f"Unsupported value type for Cypher literal: {type(value)}")


def to_cypher_map(d: dict) -> str:
    """Convert a Python dict to a Cypher map literal."""
    items = [f"{k}: {to_cypher_literal(v)}" for k, v in d.items()]
    return "{" + ", ".join(items) + "}"


def generate_cypher(nodes: list[dict], rel_path: Path, cypher_path: Path):
    """Generate a standalone Cypher import file."""
    cypher_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("// Neo4j import script for Vietnamese legal documents")
    lines.append("// Generated by scripts/build_flatten.py")
    lines.append("")
    lines.append("// 1. Constraints")
    lines.append("CREATE CONSTRAINT legal_node_id IF NOT EXISTS")
    lines.append("FOR (n:LegalNode)")
    lines.append("REQUIRE n.id IS UNIQUE;")
    lines.append("")
    lines.append("CREATE CONSTRAINT legal_document_id IF NOT EXISTS")
    lines.append("FOR (n:Document)")
    lines.append("REQUIRE n.document_id IS UNIQUE;")
    lines.append("")

    # 2. Nodes batched by level.
    levels = ["Document", "Chapter", "Section", "Article", "Clause", "Point"]
    by_level = {level: [] for level in levels}
    for node in nodes:
        label = node["level"].capitalize()
        by_level.setdefault(label, []).append(node)

    lines.append("// 2. Create nodes")
    batch_size = 500
    for label in levels:
        level_nodes = by_level.get(label, [])
        if not level_nodes:
            continue
        lines.append(f"// {label} nodes ({len(level_nodes)})")
        for i in range(0, len(level_nodes), batch_size):
            batch = level_nodes[i : i + batch_size]
            map_literals = []
            for node in batch:
                props = dict(node)
                map_literals.append(to_cypher_map(props))
            lines.append("UNWIND [")
            lines.append(",\n".join(map_literals))
            lines.append("] AS row")
            lines.append(f"MERGE (n:{label}:LegalNode {{id: row.id}})")
            lines.append("SET n += row;")
            lines.append("")

    # 3. Hierarchy relationships.
    parent_rels = [
        {"child_id": n["id"], "parent_id": n["parent_key"]}
        for n in nodes
        if n["parent_key"] is not None
    ]
    if parent_rels:
        lines.append("// 3. Hierarchy relationships")
        for i in range(0, len(parent_rels), batch_size):
            batch = parent_rels[i : i + batch_size]
            map_literals = [to_cypher_map(r) for r in batch]
            lines.append("UNWIND [")
            lines.append(",\n".join(map_literals))
            lines.append("] AS row")
            lines.append("MATCH (child:LegalNode {id: row.child_id})")
            lines.append("MATCH (parent:LegalNode {id: row.parent_id})")
            lines.append("MERGE (parent)-[:HAS_CHILD]->(child);")
            lines.append("")

    # 4. Document relationships from relationship.parquet.
    try:
        import pandas as pd

        rel_df = pd.read_parquet(rel_path)
        lines.append("// 4. Document-to-document relationships")
        for _, row in rel_df.iterrows():
            doc_id = str(row["doc_id"])
            other_doc_id = str(row["other_doc_id"])
            rel_type = normalize_relationship(str(row["relationship"]))
            lines.append(
                f'MATCH (d1:Document {{document_id: "{doc_id}"}})'
            )
            lines.append(
                f'MATCH (d2:Document {{document_id: "{other_doc_id}"}})'
            )
            lines.append(f"MERGE (d1)-[:{rel_type}]->(d2);")
            lines.append("")
    except Exception as e:
        lines.append(f"// Could not generate document relationships: {e}")

    cypher_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[cypher] Wrote import script to {cypher_path}")


def main():
    root = Path(__file__).resolve().parent.parent
    artifacts_dir = root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = artifacts_dir / "parsed.json"
    if not parsed_path.exists():
        parsed_path = root / "parsed.json"
    rel_path = artifacts_dir / "relationship.parquet"
    if not rel_path.exists():
        rel_path = root / "relationship.parquet"

    flatten_path = artifacts_dir / "flatten.jsonl"
    cypher_path = artifacts_dir / "import.cypher"

    nodes = build_flatten(parsed_path, flatten_path)
    generate_cypher(nodes, rel_path, cypher_path)


if __name__ == "__main__":
    main()
