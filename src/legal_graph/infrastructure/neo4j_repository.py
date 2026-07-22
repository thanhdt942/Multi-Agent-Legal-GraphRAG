import base64
import json
import re
from datetime import date, datetime, timezone
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from legal_graph.application.models import (
    BehaviorSearchRequest,
    ComparisonSearchRequest,
    GraphExpandRequest,
    RelationsSearchRequest,
    ResolveRequest,
    SearchFilters,
)
from legal_graph.application.services import PROPOSED_WARNING, SOURCE_METADATA_WARNING
from legal_graph.core.errors import AppError


INTERNAL_PROPERTIES = {
    "embedding",
    "comparison_embedding",
    "embedding_text",
    "comparison_text",
    "embedding_text_hash",
    "comparison_text_hash",
}
INDEX_SPECS = {
    "legal_node_embedding": ("LegalNode", "embedding"),
    "article_comparison_embedding": ("Article", "comparison_embedding"),
    "behavior_embedding": ("HanhVi", "embedding"),
}
ALLOWED_RELATIONSHIPS = {
    "HAS_CHILD",
    "THAY_THE",
    "SUA_DOI",
    "TUONG_UNG",
    "DAN_CHIEU",
    "AP_DUNG_CHUYEN_TIEP",
    "LAM_HET_HIEU_LUC",
    "VI_PHAM",
}


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "iso_format"):
        return value.iso_format()
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def public_node(value: Any) -> dict[str, Any]:
    props = dict(value or {})
    for key in INTERNAL_PROPERTIES:
        props.pop(key, None)
    props["parent_id"] = props.pop("parent_key", None)
    return _json_value(props)


def document_summary(value: Any) -> dict[str, Any]:
    node = public_node(value)
    return {
        key: node.get(key)
        for key in (
            "id",
            "document_id",
            "document_number",
            "document_type",
            "document_name",
            "issued_date",
            "effective_date",
            "expiration_date",
            "issuing_authority",
            "validity_status",
            "source_url",
        )
    }


def relationship_data(record: dict[str, Any]) -> dict[str, Any]:
    props = _json_value(dict(record.get("properties") or {}))
    result = {
        "type": record["type"],
        "source_id": record["source_id"],
        "target_id": record["target_id"],
        "status": props.get("status"),
        "confidence": props.get("confidence"),
        "method": props.get("method"),
        "model": props.get("model"),
        "similarity_score": props.get("similarity_score"),
        "evidence_source": props.get("evidence_source") or props.get("evidence_new") or props.get("evidence"),
        "evidence_target": props.get("evidence_target") or props.get("evidence_old"),
        "reason": props.get("reason"),
    }
    warnings = []
    if result["status"] == "PROPOSED":
        warnings.append(PROPOSED_WARNING)
    if result["status"] is None:
        warnings.append(SOURCE_METADATA_WARNING)
    result["warnings"] = warnings
    return result


def _citation(node: dict[str, Any], hierarchy: list[Any]) -> dict[str, Any] | None:
    ancestors = [public_node(item) for item in hierarchy if item is not None]
    by_level = {item.get("level"): item for item in ancestors}
    by_level[node.get("level")] = node
    document = by_level.get("document")
    if not document:
        return None
    labels = {
        "document": "Van ban",
        "chapter": "Chuong",
        "section": "Muc",
        "article": "Dieu",
        "clause": "Khoan",
        "point": "Diem",
    }
    parts = []
    for level in ("point", "clause", "article", "section", "chapter"):
        item = by_level.get(level)
        if item and item.get("number"):
            parts.append(f"{labels[level]} {item['number']}")
    if document.get("document_name"):
        parts.append(document["document_name"])
    return {
        "node_id": node["id"],
        "document_id": document.get("document_id"),
        "document_number": document.get("document_number"),
        "document_name": document.get("document_name"),
        "chapter": (by_level.get("chapter") or {}).get("number"),
        "section": (by_level.get("section") or {}).get("number"),
        "article": (by_level.get("article") or {}).get("number"),
        "clause": (by_level.get("clause") or {}).get("number"),
        "point": (by_level.get("point") or {}).get("number"),
        "display": " ".join(parts),
        "quote": node.get("content") or "",
        "source_url": document.get("source_url"),
        "validity_status": document.get("validity_status"),
        "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _encode_cursor(name: str, node_id: str) -> str:
    raw = json.dumps([name, node_id], ensure_ascii=False).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(cursor: str | None) -> tuple[str | None, str | None]:
    if not cursor:
        return None, None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        name, node_id = json.loads(base64.urlsafe_b64decode(padded))
        return str(name), str(node_id)
    except Exception as error:
        raise AppError("INVALID_REQUEST", "Invalid pagination cursor") from error


class Neo4jLegalGraphRepository:
    def __init__(self, driver: AsyncDriver, database: str, dimensions: int) -> None:
        self.driver = driver
        self.database = database
        self.dimensions = dimensions

    @classmethod
    def create(
        cls, uri: str, credentials: tuple[str, str], database: str, dimensions: int
    ) -> "Neo4jLegalGraphRepository":
        return cls(AsyncGraphDatabase.driver(uri, auth=credentials), database, dimensions)

    async def close(self) -> None:
        await self.driver.close()

    async def _read(self, query: str, **parameters: Any) -> list[dict[str, Any]]:
        async def work(tx: Any) -> list[dict[str, Any]]:
            result = await tx.run(query, **parameters)
            return [dict(record) async for record in result]

        try:
            async with self.driver.session(database=self.database) as session:
                return await session.execute_read(work)
        except ServiceUnavailable as error:
            raise AppError(
                "NEO4J_UNAVAILABLE", "Neo4j is unavailable", status_code=503, retryable=True
            ) from error
        except Neo4jError as error:
            raise AppError("NEO4J_QUERY_FAILED", "Neo4j query failed", status_code=500) from error

    async def _write(self, query: str, **parameters: Any) -> None:
        async def work(tx: Any) -> None:
            result = await tx.run(query, **parameters)
            await result.consume()

        async with self.driver.session(database=self.database) as session:
            await session.execute_write(work)

    async def health(self) -> bool:
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def ensure_indexes(self) -> None:
        rows = await self._read(
            "SHOW INDEXES YIELD name, type, options WHERE type = 'VECTOR' "
            "RETURN name, options"
        )
        for row in rows:
            if row["name"] not in INDEX_SPECS:
                continue
            configured = (row.get("options") or {}).get("indexConfig", {}).get("vector.dimensions")
            if configured is not None and int(configured) != self.dimensions:
                raise AppError(
                    "EMBEDDING_MODEL_MISMATCH",
                    f"Index {row['name']} expects {configured} dimensions, configured {self.dimensions}",
                    status_code=409,
                )
        await self._write(
            "CREATE FULLTEXT INDEX legal_node_fulltext IF NOT EXISTS "
            "FOR (n:LegalNode) ON EACH [n.title, n.content, n.document_name, n.document_number]"
        )

    async def schema(self, include_counts: bool = False) -> dict[str, Any]:
        labels = ["Document", "Chapter", "Section", "Article", "Clause", "Point", "HanhVi"]
        properties = {
            "LegalNode": ["id", "document_id", "level", "number", "title", "content", "order", "parent_id"],
            "Document": ["document_number", "document_type", "document_name", "issued_date", "effective_date", "expiration_date", "issuing_authority", "validity_status", "source_url"],
            "HanhVi": ["id", "canonical_text", "actor", "action", "object", "condition", "status", "confidence"],
        }
        result: dict[str, Any] = {
            "labels": labels,
            "properties": properties,
            "relationships": [
                {"type": rel, "direction": "OUTGOING"} for rel in sorted(ALLOWED_RELATIONSHIPS)
            ],
        }
        if include_counts:
            rows = await self._read(
                "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS count"
            )
            result["counts"] = {row["label"]: row["count"] for row in rows}
        return result

    async def list_documents(self, **kwargs: Any) -> dict[str, Any]:
        cursor_name, cursor_id = _decode_cursor(kwargs.get("cursor"))
        limit = kwargs.get("limit", 20)
        rows = await self._read(
            """
            MATCH (d:Document)
            WHERE ($q IS NULL OR toLower(coalesce(d.document_name, '')) CONTAINS toLower($q)
                   OR toLower(coalesce(d.document_number, '')) CONTAINS toLower($q))
              AND ($document_type IS NULL OR d.document_type = $document_type)
              AND ($validity_status IS NULL OR d.validity_status = $validity_status)
              AND ($issuing_authority IS NULL OR d.issuing_authority = $issuing_authority)
              AND ($issued_from IS NULL OR d.issued_date >= $issued_from)
              AND ($issued_to IS NULL OR d.issued_date <= $issued_to)
              AND ($cursor_name IS NULL OR coalesce(d.document_name, '') > $cursor_name
                   OR (coalesce(d.document_name, '') = $cursor_name AND d.id > $cursor_id))
            RETURN d ORDER BY coalesce(d.document_name, ''), d.id LIMIT $fetch_limit
            """,
            q=kwargs.get("q"),
            document_type=kwargs.get("document_type"),
            validity_status=kwargs.get("validity_status"),
            issuing_authority=kwargs.get("issuing_authority"),
            issued_from=kwargs.get("issued_from").isoformat() if kwargs.get("issued_from") else None,
            issued_to=kwargs.get("issued_to").isoformat() if kwargs.get("issued_to") else None,
            cursor_name=cursor_name,
            cursor_id=cursor_id,
            fetch_limit=limit + 1,
        )
        has_more = len(rows) > limit
        rows = rows[:limit]
        items = [document_summary(row["d"]) for row in rows]
        next_cursor = None
        if has_more and items:
            next_cursor = _encode_cursor(items[-1].get("document_name") or "", items[-1]["id"])
        return {"items": items, "page": {"limit": limit, "next_cursor": next_cursor, "has_more": has_more}}

    async def get_document(self, document_id: str, **kwargs: Any) -> dict[str, Any] | None:
        rows = await self._read("MATCH (d:Document {document_id: $id}) RETURN d", id=document_id)
        if not rows:
            return None
        result: dict[str, Any] = {"document": document_summary(rows[0]["d"])}
        if kwargs.get("include_relations"):
            relation_request = RelationsSearchRequest(
                source={"document_ids": [document_id]},
                statuses=[kwargs.get("relation_status", "VERIFIED")],
            )
            result["relations"] = (await self.relations(relation_request))["items"]
        return result

    async def outline(self, document_id: str, depth: int, include_content: bool) -> dict[str, Any] | None:
        doc = await self.get_document(document_id)
        if not doc:
            return None
        rows = await self._read(
            f"""
            MATCH (d:Document {{document_id: $id}})-[:HAS_CHILD*1..{depth}]->(n:LegalNode)
            RETURN n ORDER BY n.id
            """,
            id=document_id,
        )
        nodes = [public_node(row["n"]) for row in rows]
        if not include_content:
            for node in nodes:
                node.pop("content", None)
        by_id = {node["id"]: {"node": node, "children": []} for node in nodes}
        roots = []
        for item in by_id.values():
            parent = by_id.get(item["node"].get("parent_id"))
            (parent["children"] if parent else roots).append(item)
        for item in by_id.values():
            item["children"].sort(key=lambda child: (child["node"].get("order") or 0, child["node"]["id"]))
        return {"document": doc["document"], "outline": roots, "truncated": False}

    async def resolve(self, request: ResolveRequest) -> list[dict[str, Any]]:
        lowered = request.reference.casefold()
        patterns = {
            "article": re.search(r"(?:điều|dieu)\s+([\w-]+)", lowered),
            "clause": re.search(r"(?:khoản|khoan)\s+([\w-]+)", lowered),
            "point": re.search(r"(?:điểm|diem)\s+([a-zđ])", lowered),
        }
        if not any(patterns.values()) and not request.hints.document_id and not request.hints.document_number:
            return []
        rows = await self._read(
            """
            MATCH (n:LegalNode)
            WHERE ($document_id IS NULL OR n.document_id = $document_id)
              AND ($document_number IS NULL OR EXISTS {
                    MATCH (d:Document {document_id: n.document_id})
                    WHERE d.document_number = $document_number })
              AND ($article IS NULL OR EXISTS {
                    MATCH (a:Article {document_id: n.document_id, number: $article})
                    WHERE a = n OR (a)-[:HAS_CHILD*1..2]->(n) })
              AND ($clause IS NULL OR (n.level IN ['clause', 'point'] AND EXISTS {
                    MATCH (c:Clause {document_id: n.document_id, number: $clause})
                    WHERE c = n OR (c)-[:HAS_CHILD]->(n) }))
              AND ($point IS NULL OR (n.level = 'point' AND n.number = $point))
            RETURN n LIMIT $limit
            """,
            document_id=request.hints.document_id,
            document_number=request.hints.document_number,
            article=patterns["article"].group(1) if patterns["article"] else None,
            clause=patterns["clause"].group(1) if patterns["clause"] else None,
            point=patterns["point"].group(1) if patterns["point"] else None,
            limit=request.limit,
        )
        hydrated = await self.hydrate_hits(
            [{"node_id": row["n"]["id"], "score": 1.0} for row in rows]
        )
        return [
            {"node": hit["node"], "citation": hit["citation"], "confidence": 1.0, "match_type": "EXACT"}
            for hit in hydrated
        ]

    async def get_node(self, node_id: str, **kwargs: Any) -> dict[str, Any] | None:
        hydrated = await self.hydrate_hits([{"node_id": node_id, "score": 1.0}])
        if not hydrated:
            return None
        result = {"node": hydrated[0]["node"], "citation": hydrated[0]["citation"]}
        if kwargs.get("include_ancestors", True):
            result["ancestors"] = hydrated[0].get("ancestors", [])
        if kwargs.get("include_children"):
            rows = await self._read(
                "MATCH (:LegalNode {id: $id})-[:HAS_CHILD]->(n) RETURN n ORDER BY n.order", id=node_id
            )
            result["children"] = [public_node(row["n"]) for row in rows]
        if kwargs.get("include_relations"):
            request = RelationsSearchRequest(
                source={"node_ids": [node_id]}, statuses=[kwargs.get("relation_status", "VERIFIED")]
            )
            result["relations"] = (await self.relations(request))["items"]
        return result

    async def context(self, node_id: str, **kwargs: Any) -> dict[str, Any] | None:
        base = await self.get_node(node_id, include_ancestors=kwargs.get("ancestors", True))
        if not base:
            return None
        depth = kwargs.get("descendant_depth", 1)
        max_nodes = kwargs.get("max_nodes", 50)
        rows = []
        if depth:
            rows.extend(await self._read(
                f"MATCH (:LegalNode {{id: $id}})-[:HAS_CHILD*1..{depth}]->(n) RETURN n ORDER BY n.id LIMIT $limit",
                id=node_id, limit=max_nodes + 1,
            ))
        if kwargs.get("siblings"):
            rows.extend(await self._read(
                "MATCH (p)-[:HAS_CHILD]->(:LegalNode {id: $id}) MATCH (p)-[:HAS_CHILD]->(n) "
                "WHERE n.id <> $id RETURN n ORDER BY n.order LIMIT $limit",
                id=node_id, limit=max_nodes + 1,
            ))
        unique = {row["n"]["id"]: public_node(row["n"]) for row in rows}
        values = list(unique.values())
        truncated = len(values) > max_nodes
        included = values[:max_nodes]
        if not kwargs.get("include_content", True):
            base["node"].pop("content", None)
            for node in included:
                node.pop("content", None)
        return {**base, "related_nodes": included, "truncated": truncated, "omitted_count": max(0, len(values) - max_nodes)}

    @staticmethod
    def _filter_parameters(filters: SearchFilters) -> dict[str, Any]:
        return {
            "document_ids": filters.document_ids or None,
            "document_numbers": filters.document_numbers or None,
            "levels": [item.value for item in filters.levels] or None,
            "validity_statuses": filters.validity_statuses or None,
            "issued_from": filters.issued_from.isoformat() if filters.issued_from else None,
            "issued_to": filters.issued_to.isoformat() if filters.issued_to else None,
        }

    async def vector_search(self, embedding: list[float], index: str, filters: SearchFilters, candidate_k: int, min_score: float) -> list[dict[str, Any]]:
        if index not in INDEX_SPECS:
            raise AppError("INVALID_FILTER", "Unsupported vector index")
        label, _ = INDEX_SPECS[index]
        source_match = "OPTIONAL MATCH (node:HanhVi)-[:VI_PHAM]->(source:LegalNode)" if label == "HanhVi" else "WITH node, score, node AS source"
        rows = await self._read(
            f"""
            CALL db.index.vector.queryNodes('{index}', $candidate_k, $embedding)
            YIELD node, score
            {source_match}
            OPTIONAL MATCH (document:Document {{document_id: source.document_id}})
            WHERE score >= $min_score
              AND ($document_ids IS NULL OR source.document_id IN $document_ids)
              AND ($document_numbers IS NULL OR document.document_number IN $document_numbers)
              AND ($levels IS NULL OR source.level IN $levels)
              AND ($validity_statuses IS NULL OR document.validity_status IN $validity_statuses)
              AND ($issued_from IS NULL OR document.issued_date >= $issued_from)
              AND ($issued_to IS NULL OR document.issued_date <= $issued_to)
            RETURN source.id AS node_id, score, node.id AS semantic_node_id
            ORDER BY score DESC LIMIT $candidate_k
            """,
            embedding=embedding,
            candidate_k=candidate_k,
            min_score=min_score,
            **self._filter_parameters(filters),
        )
        return rows

    async def keyword_search(self, query: str, filters: SearchFilters, candidate_k: int) -> list[dict[str, Any]]:
        # Lucene-reserved punctuation is whitespace-normalized instead of passed as syntax.
        safe_query = re.sub(r"[+\-&|!(){}\[\]^\"~*?:\\/]", " ", query).strip()
        if not safe_query:
            return []
        rows = await self._read(
            """
            CALL db.index.fulltext.queryNodes('legal_node_fulltext', $query, {limit: $candidate_k})
            YIELD node, score
            OPTIONAL MATCH (document:Document {document_id: node.document_id})
            WHERE ($document_ids IS NULL OR node.document_id IN $document_ids)
              AND ($document_numbers IS NULL OR document.document_number IN $document_numbers)
              AND ($levels IS NULL OR node.level IN $levels)
              AND ($validity_statuses IS NULL OR document.validity_status IN $validity_statuses)
              AND ($issued_from IS NULL OR document.issued_date >= $issued_from)
              AND ($issued_to IS NULL OR document.issued_date <= $issued_to)
            RETURN node.id AS node_id, score ORDER BY score DESC LIMIT $candidate_k
            """,
            query=safe_query,
            candidate_k=candidate_k,
            **self._filter_parameters(filters),
        )
        return rows

    async def hydrate_hits(self, hits: list[dict[str, Any]], include_ancestors: bool = True) -> list[dict[str, Any]]:
        if not hits:
            return []
        ids = [hit["node_id"] for hit in hits]
        rows = await self._read(
            """
            UNWIND $ids AS node_id
            MATCH (n:LegalNode {id: node_id})
            OPTIONAL MATCH path=(d:Document)-[:HAS_CHILD*0..5]->(n)
            WITH node_id, n, path ORDER BY length(path) DESC
            WITH node_id, n, collect(nodes(path))[0] AS hierarchy
            RETURN node_id, n, hierarchy
            """,
            ids=ids,
        )
        by_id = {row["node_id"]: row for row in rows}
        hydrated = []
        for hit in hits:
            row = by_id.get(hit["node_id"])
            if not row:
                continue
            node = public_node(row["n"])
            hierarchy = row.get("hierarchy") or []
            item = dict(hit)
            item.update(
                {
                    "node": node,
                    "matched_text": node.get("content") or node.get("title") or "",
                    "citation": _citation(node, hierarchy),
                    "warnings": [],
                }
            )
            if include_ancestors:
                item["ancestors"] = [
                    public_node(ancestor) for ancestor in hierarchy if ancestor["id"] != node["id"]
                ]
            hydrated.append(item)
        return hydrated

    @staticmethod
    def _relationship_fragment(values: list[Any]) -> str:
        names = [item.value if hasattr(item, "value") else str(item) for item in values]
        if not names or any(name not in ALLOWED_RELATIONSHIPS for name in names):
            raise AppError("INVALID_FILTER", "Unsupported relationship type")
        return "|".join(names)

    async def expand(self, request: GraphExpandRequest) -> dict[str, Any]:
        relation_fragment = self._relationship_fragment(request.relationships)
        arrows = {
            "OUTGOING": ("-", "->"),
            "INCOMING": ("<-", "-"),
            "BOTH": ("-", "-"),
        }[request.direction]
        rows = await self._read(
            f"""
            MATCH (seed {{id: $seed_id}})
            MATCH path=(seed){arrows[0]}[:{relation_fragment}*1..{request.depth}]{arrows[1]}(target)
            WHERE all(r IN relationships(path) WHERE
                (r.status IS NULL OR r.status IN $statuses)
                AND (r.confidence IS NULL OR r.confidence >= $min_confidence))
            RETURN path LIMIT $path_limit
            """,
            seed_id=request.seed_ids[0],
            statuses=[status.value for status in request.relationship_statuses],
            min_confidence=request.min_confidence,
            path_limit=request.max_nodes * 3 + 1,
        )
        # Query each seed independently so path semantics remain bounded and predictable.
        for seed_id in request.seed_ids[1:]:
            rows.extend(await self._read(
                f"""
                MATCH (seed {{id: $seed_id}})
                MATCH path=(seed){arrows[0]}[:{relation_fragment}*1..{request.depth}]{arrows[1]}(target)
                WHERE all(r IN relationships(path) WHERE
                    (r.status IS NULL OR r.status IN $statuses)
                    AND (r.confidence IS NULL OR r.confidence >= $min_confidence))
                RETURN path LIMIT $path_limit
                """,
                seed_id=seed_id,
                statuses=[status.value for status in request.relationship_statuses],
                min_confidence=request.min_confidence,
                path_limit=request.max_nodes * 3 + 1,
            ))
        nodes: dict[str, dict[str, Any]] = {}
        relations: dict[str, dict[str, Any]] = {}
        paths = []
        warnings = []
        for row in rows:
            path = row["path"]
            node_ids = []
            for node in path.nodes:
                item = public_node(node)
                if len(nodes) < request.max_nodes or item["id"] in nodes:
                    nodes[item["id"]] = item
                    node_ids.append(item["id"])
            rel_types = []
            for rel in path.relationships:
                source_id = path.nodes[rel.start_node.element_id == path.nodes[-1].element_id and -1 or 0]["id"] if False else None
                # Neo4j relationship endpoint IDs are resolved from adjacent path nodes below.
                rel_types.append(rel.type)
            for index, rel in enumerate(path.relationships):
                data = relationship_data(
                    {
                        "type": rel.type,
                        "source_id": path.nodes[index]["id"],
                        "target_id": path.nodes[index + 1]["id"],
                        "properties": dict(rel),
                    }
                )
                key = f"{data['source_id']}|{data['type']}|{data['target_id']}"
                data["id"] = f"rel_{abs(hash(key)):x}"
                relations[key] = data
                warnings.extend(w for w in data["warnings"] if w not in warnings)
            if request.include_paths and len(node_ids) == len(path.nodes):
                paths.append({"node_ids": node_ids, "relationship_types": rel_types, "length": len(rel_types)})
        truncated = len(rows) > request.max_nodes * 3 or len(nodes) >= request.max_nodes
        return {"nodes": list(nodes.values()), "relationships": list(relations.values()), "paths": paths, "truncated": truncated, "warnings": warnings}

    async def relations(self, request: RelationsSearchRequest) -> dict[str, Any]:
        fragment = self._relationship_fragment(request.types)
        cursor_source, cursor_target = _decode_cursor(request.cursor)
        rows = await self._read(
            f"""
            MATCH (source)-[r:{fragment}]->(target)
            WHERE ($source_documents IS NULL OR source.document_id IN $source_documents)
              AND ($source_nodes IS NULL OR source.id IN $source_nodes)
              AND ($target_documents IS NULL OR target.document_id IN $target_documents)
              AND ($target_nodes IS NULL OR target.id IN $target_nodes)
              AND (r.status IS NULL OR r.status IN $statuses)
              AND (r.confidence IS NULL OR r.confidence >= $min_confidence)
              AND ($cursor_source IS NULL OR source.id > $cursor_source
                   OR (source.id = $cursor_source AND target.id > $cursor_target))
            RETURN source, target, type(r) AS type, properties(r) AS properties,
                   source.id AS source_id, target.id AS target_id
            ORDER BY source.id, target.id LIMIT $fetch_limit
            """,
            source_documents=request.source.document_ids or None,
            source_nodes=request.source.node_ids or None,
            target_documents=request.target.document_ids or None,
            target_nodes=request.target.node_ids or None,
            statuses=[status.value for status in request.statuses],
            min_confidence=request.min_confidence,
            cursor_source=cursor_source,
            cursor_target=cursor_target,
            fetch_limit=request.limit + 1,
        )
        has_more = len(rows) > request.limit
        rows = rows[: request.limit]
        source_hits = await self.hydrate_hits([{"node_id": row["source_id"], "score": 1.0} for row in rows])
        target_hits = await self.hydrate_hits([{"node_id": row["target_id"], "score": 1.0} for row in rows])
        sources = {hit["node"]["id"]: hit for hit in source_hits}
        targets = {hit["node"]["id"]: hit for hit in target_hits}
        items = []
        for row in rows:
            relation = relationship_data(row)
            source = sources.get(row["source_id"])
            target = targets.get(row["target_id"])
            items.append({
                "source": source["node"] if source else public_node(row["source"]),
                "target": target["node"] if target else public_node(row["target"]),
                "relationship": relation,
                "source_citation": source.get("citation") if source else None,
                "target_citation": target.get("citation") if target else None,
                "warnings": relation["warnings"],
            })
        next_cursor = _encode_cursor(rows[-1]["source_id"], rows[-1]["target_id"]) if has_more and rows else None
        return {"items": items, "page": {"limit": request.limit, "next_cursor": next_cursor, "has_more": has_more}}

    async def behaviors(self, request: BehaviorSearchRequest, embedding: list[float]) -> dict[str, Any]:
        rows = await self._read(
            """
            CALL db.index.vector.queryNodes('behavior_embedding', $candidate_k, $embedding)
            YIELD node, score
            MATCH (node:HanhVi)-[r:VI_PHAM]->(source:LegalNode)
            WHERE score >= $min_score
              AND ($document_ids IS NULL OR source.document_id IN $document_ids)
              AND (node.status IN $statuses OR r.status IN $statuses)
            RETURN node, source.id AS source_id, score, properties(r) AS rel_properties
            ORDER BY score DESC LIMIT $top_k
            """,
            candidate_k=max(request.top_k * 5, 50), embedding=embedding,
            min_score=request.min_score, document_ids=request.document_ids or None,
            statuses=[status.value for status in request.statuses], top_k=request.top_k,
        )
        sources = await self.hydrate_hits([{"node_id": row["source_id"], "score": row["score"]} for row in rows])
        by_id = {item["node"]["id"]: item for item in sources}
        hits = []
        for row in rows:
            behavior = public_node(row["node"])
            source = by_id.get(row["source_id"])
            warnings = [PROPOSED_WARNING] if behavior.get("status") == "PROPOSED" else []
            hits.append({"behavior": behavior, "score": row["score"],
                         "source_node": source["node"] if request.include_source and source else None,
                         "citation": source["citation"] if request.include_source and source else None,
                         "warnings": warnings})
        return {"hits": hits}

    async def comparisons(self, request: ComparisonSearchRequest, embedding: list[float] | None) -> dict[str, Any]:
        relation_request = RelationsSearchRequest(
            source={"document_ids": [request.source_document_id], "node_ids": request.source_node_ids},
            target={"document_ids": [request.target_document_id]},
            types=request.relationship_types, statuses=request.statuses, limit=request.top_k,
        )
        graph_items = (await self.relations(relation_request))["items"]
        items = [{**item, "match_origin": "GRAPH_RELATION", "confidence": item["relationship"].get("confidence")} for item in graph_items]
        if embedding is not None and len(items) < request.top_k:
            filters = SearchFilters(document_ids=[request.target_document_id], levels=["article"])
            candidates = await self.vector_search(embedding, "article_comparison_embedding", filters, request.top_k * 5, -1)
            targets = await self.hydrate_hits(candidates)
            source_ids = request.source_node_ids
            if not source_ids:
                source_rows = await self._read(
                    "MATCH (n:Article {document_id: $id}) RETURN n.id AS id ORDER BY n.order LIMIT 1",
                    id=request.source_document_id,
                )
                source_ids = [row["id"] for row in source_rows]
            source = (await self.hydrate_hits([{"node_id": source_ids[0], "score": 1.0}])) if source_ids else []
            existing = {(item["source"]["id"], item["target"]["id"]) for item in items}
            for target in targets:
                if not source or (source[0]["node"]["id"], target["node"]["id"]) in existing:
                    continue
                items.append({"source": source[0]["node"], "target": target["node"],
                              "relationship": None, "source_citation": source[0]["citation"],
                              "target_citation": target["citation"], "match_origin": "VECTOR_CANDIDATE",
                              "confidence": target["score"],
                              "warnings": ["VECTOR_CANDIDATE chi la ung vien ngu nghia, khong phai quan he phap ly da xac nhan"]})
                if len(items) >= request.top_k:
                    break
        return {"items": items[: request.top_k]}
