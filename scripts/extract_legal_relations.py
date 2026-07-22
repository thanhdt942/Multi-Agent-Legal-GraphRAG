#!/usr/bin/env python3
"""Extract cross-version relations between the 2024 and 2013 Land Laws.

OpenAI results are cached per new Article in artifacts/llm_article_results.jsonl.
A completed cache entry, including an empty result, is never requested again
unless the model, source text, or candidate Article IDs change.
"""

import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI, RateLimitError

from neo4j_client import get_credentials, get_driver


NEW_DOC_ID = "177815"
OLD_DOC_ID = "32833"
TOP_K = int(os.environ.get("ARTICLE_CANDIDATE_TOP_K", "3"))
CONFIDENCE_THRESHOLD = float(os.environ.get("RELATION_CONFIDENCE_THRESHOLD", "0.85"))
EXTRACTION_MODEL = os.environ.get("OPENAI_EXTRACTION_MODEL", "gpt-5-nano")
ALLOWED_RELATIONS = {"THAY_THE", "SUA_DOI", "TUONG_UNG", "DAN_CHIEU", "NONE"}


def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=api_key)


def load_articles(driver, document_id: str) -> list[dict]:
    with driver.session() as session:
        result = session.run(
            """
            MATCH (n:Article {document_id: $document_id})
            RETURN n.id AS id, n.number AS number, n.title AS title,
                   n.comparison_text AS comparison_text,
                   n.comparison_embedding AS embedding
            ORDER BY toInteger(n.number), n.order
            """,
            document_id=document_id,
        )
        return [dict(record) for record in result]


def load_provisions(driver, document_id: str) -> list[dict]:
    with driver.session() as session:
        result = session.run(
            """
            MATCH (n:LegalNode {document_id: $document_id})
            WHERE n.level IN ['article', 'clause', 'point']
            RETURN n.id AS id, n.level AS level, n.number AS number,
                   n.title AS title, n.content AS content,
                   n.parent_key AS parent_key
            """,
            document_id=document_id,
        )
        return [dict(record) for record in result]


def find_candidates(driver, new_article: dict, top_k: int = TOP_K) -> list[dict]:
    with driver.session() as session:
        result = session.run(
            """
            CALL db.index.vector.queryNodes(
                'article_comparison_embedding', $search_k, $embedding
            ) YIELD node, score
            WHERE node:Article AND node.document_id = $old_doc_id
            RETURN node.id AS id, node.number AS number,
                   node.comparison_text AS comparison_text, score
            ORDER BY score DESC
            LIMIT $top_k
            """,
            search_k=max(top_k * 5, 25),
            embedding=new_article["embedding"],
            old_doc_id=OLD_DOC_ID,
            top_k=top_k,
        )
        return [dict(record) for record in result]


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_cache_key(article: dict, candidates: list[dict]) -> str:
    payload = {
        "model": EXTRACTION_MODEL,
        "source_id": article["id"],
        "source_text_hash": text_hash(article.get("comparison_text") or ""),
        "candidate_ids": [candidate["id"] for candidate in candidates],
        "prompt_version": 2,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_jsonl_latest(path: Path, key_field: str) -> dict[str, dict]:
    records = {}
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get(key_field)
            if key:
                records[key] = record
    return records


def write_jsonl_atomic(path: Path, records: list[dict]):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def build_prompt(new_article: dict, candidates: list[dict]) -> str:
    parts = [
        "Đối chiếu Điều của Luật Đất đai 2024 với ba Điều ứng viên của Luật Đất đai 2013.",
        "Chỉ trả quan hệ khi nội dung thể hiện rõ. Dùng NONE nếu chỉ gần chủ đề hoặc không chắc chắn.",
        "THAY_THE: quy định mới thay thế toàn bộ quy định cũ.",
        "SUA_DOI: quy định mới giữ nội dung lõi nhưng thay đổi/bổ sung nội dung đáng kể.",
        "TUONG_UNG: cùng chức năng pháp lý nhưng không đủ căn cứ gọi là sửa đổi/thay thế.",
        "DAN_CHIEU: quy định mới viện dẫn hoặc tiếp tục áp dụng quy định cũ.",
        "Evidence phải là trích dẫn nguyên văn ngắn từ dữ liệu được cung cấp.",
        "",
        f"ĐIỀU MỚI ID={new_article['id']}",
        new_article["comparison_text"],
        "",
        "CÁC ĐIỀU CŨ ỨNG VIÊN:",
    ]
    for candidate in candidates:
        parts.extend(
            [
                "",
                f"ID={candidate['id']} | similarity={candidate['score']:.6f}",
                candidate["comparison_text"],
            ]
        )
    parts.extend(
        [
            "",
            "Trả JSON: {\"matches\": [{\"old_article_id\": \"ID chính xác đã cung cấp\", "
            "\"relationship\": \"THAY_THE|SUA_DOI|TUONG_UNG|DAN_CHIEU|NONE\", "
            "\"confidence\": 0.0, \"reason\": \"...\", "
            "\"evidence_new\": \"...\", \"evidence_old\": \"...\"}]}",
            "Mỗi candidate phải có đúng một phần tử matches và old_article_id phải giữ nguyên ID đã cung cấp.",
        ]
    )
    return "\n".join(parts)


def call_llm(client, prompt: str, max_retries: int = 5) -> tuple[dict, dict]:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=EXTRACTION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Bạn là chuyên gia đối chiếu văn bản pháp luật Việt Nam. "
                            "Luôn trả JSON hợp lệ và không suy diễn quan hệ pháp lý khi thiếu căn cứ."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            usage = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
                "completion_tokens": getattr(response.usage, "completion_tokens", None),
                "total_tokens": getattr(response.usage, "total_tokens", None),
            }
            return result, usage
        except RateLimitError:
            delay = 2**attempt
            print(f"[llm] Rate limited; retrying in {delay}s", flush=True)
            time.sleep(delay)
        except Exception as error:
            if attempt == max_retries - 1:
                raise
            print(f"[llm] {type(error).__name__}; retrying", flush=True)
            time.sleep(2**attempt)
    raise RuntimeError("LLM retries exhausted")


def request_article(client, article: dict, candidates: list[dict], cache_key: str) -> dict:
    try:
        result, usage = call_llm(client, build_prompt(article, candidates))
        return {
            "cache_key": cache_key,
            "source_id": article["id"],
            "source_text_hash": text_hash(article.get("comparison_text") or ""),
            "candidate_ids": [candidate["id"] for candidate in candidates],
            "model": EXTRACTION_MODEL,
            "status": "COMPLETED",
            "result": result,
            "usage": usage,
        }
    except Exception as error:
        return {
            "cache_key": cache_key,
            "source_id": article["id"],
            "source_text_hash": text_hash(article.get("comparison_text") or ""),
            "candidate_ids": [candidate["id"] for candidate in candidates],
            "model": EXTRACTION_MODEL,
            "status": "FAILED",
            "error": f"{type(error).__name__}: {error}",
        }


def normalize_text(value) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    elif isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False)
    elif value is None:
        value = ""
    elif not isinstance(value, str):
        value = str(value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def evidence_exists(evidence: str, text: str) -> bool:
    normalized_evidence = normalize_text(evidence)
    if not normalized_evidence:
        return False
    return normalized_evidence in normalize_text(text)


def find_child(
    children_by_parent: dict[str, list[dict]],
    parent_id: str,
    level: str,
    number: str,
) -> dict | None:
    return next(
        (
            node
            for node in children_by_parent.get(parent_id, [])
            if node["level"] == level and node["number"] == number
        ),
        None,
    )


def extract_rule_relations(
    new_articles: list[dict],
    old_articles: list[dict],
    new_provisions: list[dict],
    old_provisions: list[dict],
) -> list[dict]:
    old_by_number = {article["number"]: article for article in old_articles}
    new_by_number = {article["number"]: article for article in new_articles}
    old_children = {}
    new_children = {}
    for node in old_provisions:
        old_children.setdefault(node.get("parent_key"), []).append(node)
    for node in new_provisions:
        new_children.setdefault(node.get("parent_key"), []).append(node)
    relations = []

    # Explicit old-law provision references in transition provisions.
    pattern = re.compile(
        r"(?:(điểm)\s+([a-zđ])\s+)?(?:(khoản)\s+(\d+)\s+)?Điều\s+(\d+)"
        r"(?=[^.;\n]{0,180}(?:45/2013/QH13|Luật Đất đai số 45/2013))",
        re.IGNORECASE,
    )
    for source in new_provisions:
        text = " ".join(
            part for part in (source.get("title"), source.get("content")) if part
        )
        for match in pattern.finditer(text):
            old_article = old_by_number.get(match.group(5))
            if not old_article:
                continue
            target = old_article
            clause_number = match.group(4)
            point_number = match.group(2)
            if clause_number:
                target = find_child(
                    old_children, old_article["id"], "clause", clause_number
                )
            if target and point_number:
                target = find_child(old_children, target["id"], "point", point_number)
            if not target:
                continue
            evidence_start = match.start()
            evidence_end = min(len(text), match.end() + 180)
            evidence = text[evidence_start:evidence_end].split("\n", 1)[0]
            relationship = (
                "AP_DUNG_CHUYEN_TIEP"
                if "tiếp tục" in normalize_text(text)
                else "DAN_CHIEU"
            )
            relations.append(
                {
                    "source_id": source["id"],
                    "target_id": target["id"],
                    "relationship": relationship,
                    "status": "VERIFIED",
                    "confidence": 1.0,
                    "method": "RULE",
                    "model": None,
                    "similarity_score": None,
                    "evidence_new": evidence,
                    "evidence_old": None,
                    "reason": "Tham chiếu trực tiếp đến quy định của Luật 45/2013/QH13",
                }
            )

    # Clause 4, Article 252 explicitly terminates the old law.
    article_252 = new_by_number.get("252")
    clause_252_4 = (
        find_child(new_children, article_252["id"], "clause", "4")
        if article_252
        else None
    )
    if clause_252_4:
        relations.append(
            {
                "source_id": clause_252_4["id"],
                "target_id": "vbpl:32833",
                "relationship": "LAM_HET_HIEU_LUC",
                "status": "VERIFIED",
                "confidence": 1.0,
                "method": "RULE",
                "model": None,
                "similarity_score": None,
                "evidence_new": "Luật Đất đai số 45/2013/QH13 ... hết hiệu lực kể từ ngày Luật này có hiệu lực thi hành.",
                "evidence_old": None,
                "reason": "Khoản 4 Điều 252 quy định trực tiếp hiệu lực của Luật 45/2013/QH13",
            }
        )

    # These Articles have the same explicit legal function in the two laws.
    article_11 = new_by_number.get("11")
    article_12 = old_by_number.get("12")
    if article_11 and article_12:
        relations.append(
            {
                "source_id": article_11["id"],
                "target_id": article_12["id"],
                "relationship": "TUONG_UNG",
                "status": "VERIFIED",
                "confidence": 1.0,
                "method": "RULE",
                "model": None,
                "similarity_score": None,
                "evidence_new": article_11["title"],
                "evidence_old": article_12["title"],
                "reason": "Hai Điều cùng quy định danh mục hành vi bị nghiêm cấm",
            }
        )

    unique = {}
    for relation in relations:
        key = (relation["source_id"], relation["target_id"], relation["relationship"])
        unique[key] = relation
    return list(unique.values())


def materialize_llm_relations(
    new_by_id: dict[str, dict],
    old_by_id: dict[str, dict],
    candidates_by_source: dict[str, list[dict]],
    cache_by_key: dict[str, dict],
) -> list[dict]:
    relations = []
    for source_id, article in new_by_id.items():
        candidates = candidates_by_source.get(source_id, [])
        if not candidates:
            continue
        cache_key = make_cache_key(article, candidates)
        cached = cache_by_key.get(cache_key)
        if not cached or cached.get("status") != "COMPLETED":
            continue
        candidate_by_id = {candidate["id"]: candidate for candidate in candidates}
        for match in cached.get("result", {}).get("matches", []):
            target_id = match.get("old_article_id")
            target = old_by_id.get(target_id)
            relationship = match.get("relationship")
            confidence = float(match.get("confidence") or 0)
            status = "PROPOSED"
            reject_reason = None
            if target_id not in candidate_by_id or not target:
                status, reject_reason = "REJECTED", "target is not a supplied candidate ID"
            elif relationship not in ALLOWED_RELATIONS:
                status, reject_reason = "REJECTED", "invalid relationship"
            elif relationship == "NONE":
                status, reject_reason = "REJECTED", "no relationship"
            elif confidence < CONFIDENCE_THRESHOLD:
                status, reject_reason = "REJECTED", "below confidence threshold"
            elif not evidence_exists(match.get("evidence_new"), article["comparison_text"]):
                status, reject_reason = "REJECTED", "new evidence is not an exact quote"
            elif not evidence_exists(match.get("evidence_old"), target["comparison_text"]):
                status, reject_reason = "REJECTED", "old evidence is not an exact quote"

            relation = {
                "source_id": source_id,
                "target_id": target_id,
                "relationship": relationship,
                "status": status,
                "confidence": confidence,
                "method": "LLM",
                "model": EXTRACTION_MODEL,
                "similarity_score": candidate_by_id.get(target_id, {}).get("score"),
                "evidence_new": match.get("evidence_new"),
                "evidence_old": match.get("evidence_old"),
                "reason": match.get("reason"),
            }
            if reject_reason:
                relation["reject_reason"] = reject_reason
            relations.append(relation)
    return relations


def main():
    root = Path(__file__).resolve().parent.parent
    artifacts = root / "artifacts"
    artifacts.mkdir(exist_ok=True)
    candidates_path = artifacts / "article_candidates.jsonl"
    cache_path = artifacts / "llm_article_results.jsonl"
    relations_path = artifacts / "extracted_relations.jsonl"

    print(f"[model] Relation extraction model: {EXTRACTION_MODEL}")
    print(f"[model] Candidate embedding: text-embedding-3-small")
    print(f"[config] top_k={TOP_K}, confidence_threshold={CONFIDENCE_THRESHOLD}")
    uri, user = get_credentials()
    print(f"[config] Neo4j: {uri} as {user}")

    driver = get_driver()
    try:
        new_articles = load_articles(driver, NEW_DOC_ID)
        old_articles = load_articles(driver, OLD_DOC_ID)
        new_provisions = load_provisions(driver, NEW_DOC_ID)
        old_provisions = load_provisions(driver, OLD_DOC_ID)
        new_by_id = {article["id"]: article for article in new_articles}
        old_by_id = {article["id"]: article for article in old_articles}
        print(f"[load] new={len(new_articles)}, old={len(old_articles)}")

        candidates_by_source = {}
        candidate_records = []
        for index, article in enumerate(new_articles, 1):
            if not article.get("embedding"):
                continue
            candidates = find_candidates(driver, article)
            candidates_by_source[article["id"]] = candidates
            candidate_records.append(
                {
                    "source_id": article["id"],
                    "source_text_hash": text_hash(article.get("comparison_text") or ""),
                    "embedding_model": "text-embedding-3-small",
                    "candidates": candidates,
                }
            )
            if index % 50 == 0:
                print(f"[candidates] {index}/{len(new_articles)}")
        write_jsonl_atomic(candidates_path, candidate_records)

        cache_by_key = load_jsonl_latest(cache_path, "cache_key")
        pending = []
        for article in new_articles:
            candidates = candidates_by_source.get(article["id"], [])
            if not candidates:
                continue
            cache_key = make_cache_key(article, candidates)
            cached = cache_by_key.get(cache_key)
            if cached and cached.get("status") == "COMPLETED":
                continue
            pending.append((article, candidates, cache_key))

        print(f"[resume] completed={len(new_articles) - len(pending)}, pending={len(pending)}")
        if pending:
            client = get_openai_client()
            max_workers = int(os.environ.get("LLM_MAX_WORKERS", "10"))
            completed = 0
            with cache_path.open("a", encoding="utf-8") as cache_file:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(request_article, client, article, candidates, cache_key): article["id"]
                        for article, candidates, cache_key in pending
                    }
                    for future in as_completed(futures):
                        record = future.result()
                        cache_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                        cache_file.flush()
                        os.fsync(cache_file.fileno())
                        cache_by_key[record["cache_key"]] = record
                        completed += 1
                        print(
                            f"[llm] {completed}/{len(pending)} {record['source_id']} {record['status']}",
                            flush=True,
                        )

        rule_relations = extract_rule_relations(
            new_articles, old_articles, new_provisions, old_provisions
        )
        llm_relations = materialize_llm_relations(
            new_by_id, old_by_id, candidates_by_source, cache_by_key
        )
        all_relations = rule_relations + llm_relations
        write_jsonl_atomic(relations_path, all_relations)

        status_counts = {}
        type_counts = {}
        for relation in all_relations:
            status_counts[relation["status"]] = status_counts.get(relation["status"], 0) + 1
            rel_type = relation.get("relationship")
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        total_usage = sum(
            (record.get("usage") or {}).get("total_tokens") or 0
            for record in cache_by_key.values()
            if record.get("status") == "COMPLETED"
        )
        print(f"[save] {relations_path}: {len(all_relations)} records")
        print(f"[verify] statuses={status_counts}")
        print(f"[verify] relationships={type_counts}")
        print(f"[usage] cached total tokens={total_usage}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
