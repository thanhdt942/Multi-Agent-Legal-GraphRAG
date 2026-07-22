#!/usr/bin/env python3
"""Extract prohibited behaviors from Article 12/2013 and Article 11/2024.

Raw GPT-5-nano responses are cached by model and source text hash so a rerun
only re-validates locally unless the input changes.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI, RateLimitError

from neo4j_client import get_credentials, get_driver


EXTRACTION_MODEL = os.environ.get("OPENAI_EXTRACTION_MODEL", "gpt-5-nano")
CONFIDENCE_THRESHOLD = float(os.environ.get("BEHAVIOR_CONFIDENCE_THRESHOLD", "0.85"))
TARGETS = [("32833", "12"), ("177815", "11")]


def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=api_key)


def load_target_articles(driver) -> list[dict]:
    articles = []
    with driver.session() as session:
        for document_id, article_number in TARGETS:
            record = session.run(
                """
                MATCH (a:Article {document_id: $document_id, number: $article_number})
                OPTIONAL MATCH (a)-[:HAS_CHILD]->(c:Clause)
                WITH a, c ORDER BY c.order
                RETURN a.id AS article_id, a.document_id AS document_id,
                       a.number AS article_number, a.title AS article_title,
                       collect({id: c.id, number: c.number, content: c.content}) AS clauses
                """,
                document_id=document_id,
                article_number=article_number,
            ).single()
            if not record:
                raise RuntimeError(f"Article {article_number}/{document_id} not found")
            article = dict(record)
            article["clauses"] = [clause for clause in article["clauses"] if clause.get("id")]
            articles.append(article)
    return articles


def source_text(article: dict) -> str:
    lines = [
        f"Điều {article['article_number']}. {article['article_title']}",
    ]
    for clause in article["clauses"]:
        lines.append(
            f"SOURCE_NODE_ID={clause['id']}\nKhoản {clause['number']}. {clause['content']}"
        )
    return "\n\n".join(lines)


def cache_key(article: dict) -> str:
    payload = {
        "model": EXTRACTION_MODEL,
        "article_id": article["article_id"],
        "source_hash": hashlib.sha256(source_text(article).encode("utf-8")).hexdigest(),
        "prompt_version": 1,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def load_cache(path: Path) -> dict[str, dict]:
    records = {}
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("cache_key"):
                records[record["cache_key"]] = record
    return records


def build_prompt(article: dict) -> str:
    return f"""Trích xuất các hành vi bị nghiêm cấm từ Điều luật dưới đây.

Yêu cầu:
- Một Khoản có thể chứa nhiều hành vi; tách thành các hành vi riêng.
- source_node_id phải giữ nguyên đúng SOURCE_NODE_ID đã cung cấp.
- evidence phải là trích dẫn nguyên văn nằm trong nội dung Khoản.
- canonical_text là mô tả hành vi ngắn, độc lập và không thêm suy diễn.
- actor, action, object, condition có thể là null nếu văn bản không nêu rõ.

{source_text(article)}

Trả JSON:
{{"behaviors": [{{"source_node_id": "...", "text": "...", "canonical_text": "...", "actor": null, "action": "...", "object": "...", "condition": null, "evidence": "...", "confidence": 0.0}}]}}
"""


def call_llm(client, prompt: str, max_retries: int = 5) -> tuple[dict, dict]:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=EXTRACTION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Bạn trích xuất hành vi bị nghiêm cấm từ luật Việt Nam. "
                            "Luôn trả JSON hợp lệ, giữ nguyên source_node_id và evidence nguyên văn."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content), {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
                "completion_tokens": getattr(response.usage, "completion_tokens", None),
                "total_tokens": getattr(response.usage, "total_tokens", None),
            }
        except RateLimitError:
            time.sleep(2**attempt)
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("LLM retries exhausted")


def normalize_text(value) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    if value is None:
        value = ""
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def normalize_source_id(value) -> str:
    return str(value or "").removeprefix("SOURCE_NODE_ID=").strip()


def normalize_evidence(value) -> str:
    normalized = normalize_text(value)
    return re.sub(r"^khoản\s+\w+\.\s*", "", normalized)


def behavior_id(source_node_id: str, canonical_text: str) -> str:
    digest = hashlib.sha256(
        f"{source_node_id}\n{normalize_text(canonical_text)}".encode("utf-8")
    ).hexdigest()[:24]
    return f"hanh_vi:{digest}"


def materialize(articles: list[dict], cache: dict[str, dict]) -> list[dict]:
    output = []
    for article in articles:
        cached = cache.get(cache_key(article))
        if not cached or cached.get("status") != "COMPLETED":
            continue
        clauses = {clause["id"]: clause for clause in article["clauses"]}
        for item in cached.get("result", {}).get("behaviors", []):
            source_node_id = normalize_source_id(item.get("source_node_id"))
            clause = clauses.get(source_node_id)
            confidence = float(item.get("confidence") or 0)
            canonical_text = normalize_text(item.get("canonical_text"))
            evidence = normalize_evidence(item.get("evidence"))
            status = "PROPOSED"
            reject_reason = None
            if not clause:
                status, reject_reason = "REJECTED", "source node is not a supplied Clause"
            elif not canonical_text:
                status, reject_reason = "REJECTED", "empty canonical text"
            elif evidence not in normalize_text(clause.get("content")):
                status, reject_reason = "REJECTED", "evidence is not an exact quote"
            else:
                # The parent Articles explicitly define these Clauses as prohibited
                # behaviors; LLM is only used to normalize/split their wording.
                confidence = 1.0

            record = {
                "id": behavior_id(source_node_id or article["article_id"], canonical_text),
                "source_node_id": source_node_id,
                "document_id": article["document_id"],
                "article_id": article["article_id"],
                "text": item.get("text"),
                "canonical_text": item.get("canonical_text"),
                "actor": item.get("actor"),
                "action": item.get("action"),
                "object": item.get("object"),
                "condition": item.get("condition"),
                "evidence": item.get("evidence"),
                "confidence": confidence,
                "status": status,
                "method": "LLM",
                "model": EXTRACTION_MODEL,
                "embedding_text": (
                    f"Hành vi bị nghiêm cấm theo Điều {article['article_number']} | "
                    f"{item.get('canonical_text') or item.get('text')}"
                ),
            }
            if reject_reason:
                record["reject_reason"] = reject_reason
            output.append(record)
    return output


def write_jsonl_atomic(path: Path, records: list[dict]):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def main():
    root = Path(__file__).resolve().parent.parent
    artifacts = root / "artifacts"
    cache_path = artifacts / "llm_behavior_results.jsonl"
    output_path = artifacts / "extracted_behaviors.jsonl"

    print(f"[model] Behavior extraction model: {EXTRACTION_MODEL}")
    print(f"[config] Confidence threshold: {CONFIDENCE_THRESHOLD}")
    uri, user = get_credentials()
    print(f"[config] Neo4j: {uri} as {user}")

    driver = get_driver()
    try:
        articles = load_target_articles(driver)
    finally:
        driver.close()

    cache = load_cache(cache_path)
    pending = [article for article in articles if cache_key(article) not in cache]
    print(f"[resume] completed={len(articles) - len(pending)}, pending={len(pending)}")
    if pending:
        client = get_openai_client()
        with cache_path.open("a", encoding="utf-8") as cache_file:
            for article in pending:
                key = cache_key(article)
                try:
                    result, usage = call_llm(client, build_prompt(article))
                    record = {
                        "cache_key": key,
                        "article_id": article["article_id"],
                        "model": EXTRACTION_MODEL,
                        "status": "COMPLETED",
                        "result": result,
                        "usage": usage,
                    }
                except Exception as error:
                    record = {
                        "cache_key": key,
                        "article_id": article["article_id"],
                        "model": EXTRACTION_MODEL,
                        "status": "FAILED",
                        "error": f"{type(error).__name__}: {error}",
                    }
                cache_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                cache_file.flush()
                os.fsync(cache_file.fileno())
                cache[key] = record
                print(f"[llm] {article['article_id']} {record['status']}")

    behaviors = materialize(articles, cache)
    write_jsonl_atomic(output_path, behaviors)
    statuses = {}
    for behavior in behaviors:
        statuses[behavior["status"]] = statuses.get(behavior["status"], 0) + 1
    total_usage = sum(
        (record.get("usage") or {}).get("total_tokens") or 0
        for record in cache.values()
        if record.get("status") == "COMPLETED"
    )
    print(f"[save] {output_path}: {len(behaviors)} records")
    print(f"[verify] statuses={statuses}")
    print(f"[usage] cached total tokens={total_usage}")


if __name__ == "__main__":
    main()
