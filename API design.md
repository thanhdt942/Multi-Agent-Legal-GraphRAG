# API Design - Vietnamese Legal Graph RAG

## 1. Muc tieu

Tai lieu nay dac ta API cho ung dung Agent truy xuat knowledge graph van ban phap luat Viet Nam dang luu trong Neo4j. API gom hai lop:

1. **Retrieval API**: tim kiem ngu nghia, tim kiem ket hop, phan giai tham chieu, duyet graph va dong goi context co citation.
2. **Answer API**: dung Retrieval API de tao cau tra loi bang LLM, kem citation va dau vet truy xuat.

Nguyen tac thiet ke:

- Agent gui cau hoi dang text; API tu tao embedding bang dung model cua index.
- Moi ket luan phap ly phai co citation den noi dung goc.
- `VERIFIED` va `PROPOSED` khong duoc coi la co do tin cay nhu nhau.
- Khong mo raw Cypher endpoint cho Agent.
- API truy xuat la stateless; lich su hoi thoai duoc gui trong request khi can.
- Khong tra vector embedding trong response.

## 2. Pham vi du lieu hien tai

Graph hien co cac node:

| Label | Y nghia |
| --- | --- |
| `Document:LegalNode` | Van ban phap luat |
| `Chapter:LegalNode` | Chuong |
| `Section:LegalNode` | Muc |
| `Article:LegalNode` | Dieu |
| `Clause:LegalNode` | Khoan |
| `Point:LegalNode` | Diem |
| `HanhVi:SemanticNode` | Hanh vi bi nghiem cam da chuan hoa |

Quan he cau truc la `HAS_CHILD`. Quan he ngu nghia chinh gom:

- `THAY_THE`
- `SUA_DOI`
- `TUONG_UNG`
- `DAN_CHIEU`
- `AP_DUNG_CHUYEN_TIEP`
- `LAM_HET_HIEU_LUC`
- `VI_PHAM`

Vector index hien co:

| Index | Node/property | Muc dich |
| --- | --- | --- |
| `legal_node_embedding` | `LegalNode.embedding` | Tim quy dinh lien quan den cau hoi |
| `article_comparison_embedding` | `Article.comparison_embedding` | So sanh noi dung giua cac Dieu |
| `behavior_embedding` | `HanhVi.embedding` | Tim hanh vi bi nghiem cam |

Embedding mac dinh la `text-embedding-3-small`, 1.536 chieu, cosine similarity.

## 3. Kien truc de xuat

```text
Agent / Client
      |
      v
API Gateway: auth, rate limit, request ID
      |
      v
Graph RAG Service
      +--> Embedding Provider
      +--> Neo4j Vector Search
      +--> Neo4j Full-text/Property Search
      +--> Graph Expansion + Citation Builder
      +--> Reranker (tuy chon)
      +--> LLM Answer Generator
```

API khong de Agent truy cap truc tiep Neo4j. Tat ca relationship type, label, sort field va graph depth phai duoc validate theo allowlist.

## 4. Quy uoc chung

### 4.1 Base URL va version

```text
https://api.example.com/v1
```

Thay doi pha vo contract phai tao version moi. Them field response la thay doi tuong thich nguoc.

### 4.2 Authentication

Ho tro mot trong hai cach:

```http
Authorization: Bearer <service-token>
```

hoac:

```http
X-API-Key: <api-key>
```

Scope de xuat:

- `legal:read`: cac Retrieval API.
- `legal:answer`: Answer API.
- `legal:feedback`: gui feedback.
- `legal:admin`: xem schema/debug chi tiet.

### 4.3 Header

Request:

```http
Content-Type: application/json
Accept: application/json
X-Request-ID: req_client_generated_optional
```

Response:

```http
Content-Type: application/json; charset=utf-8
X-Request-ID: req_01J...
X-API-Version: 1
```

### 4.4 Gioi han mac dinh

| Tham so | Mac dinh | Toi da |
| --- | ---: | ---: |
| `limit` | 20 | 100 |
| `top_k` | 10 | 50 |
| `graph_depth` | 1 | 3 |
| `max_nodes` | 50 | 200 |
| `context_token_budget` | 8.000 | 24.000 |
| `timeout_ms` | 10.000 | 30.000 |

### 4.5 Pagination

Dung cursor, khong dung offset cho tap ket qua lon:

```json
{
  "items": [],
  "page": {
    "limit": 20,
    "next_cursor": "eyJzb3J0X2tleSI6Ii4uLiJ9",
    "has_more": true
  }
}
```

Cursor la opaque token va khong nen duoc client tu tao.

## 5. Data contracts

### 5.1 LegalNodeSummary

```json
{
  "id": "vbpl:177815:chapter:I:1:article:11:11:clause:1:1",
  "document_id": "177815",
  "level": "clause",
  "number": "1",
  "title": null,
  "content": "Lan dat, chiem dat, huy hoai dat.",
  "order": 1,
  "parent_id": "vbpl:177815:chapter:I:1:article:11:11"
}
```

Gia tri hop le cua `level`: `document`, `chapter`, `section`, `article`, `clause`, `point`.

Response khong tra cac property noi bo sau neu khong co quyen admin:

- `embedding`
- `comparison_embedding`
- `embedding_text`
- `comparison_text`

### 5.2 DocumentSummary

```json
{
  "id": "vbpl:177815",
  "document_id": "177815",
  "document_number": "31/2024/QH15",
  "document_type": "Luat",
  "document_name": "Luat Dat dai 2024",
  "issued_date": "2024-01-18",
  "effective_date": "2024-08-01",
  "expiration_date": null,
  "issuing_authority": "Quoc hoi",
  "validity_status": "Con hieu luc",
  "source_url": "https://vbpl.vn/..."
}
```

### 5.3 LegalCitation

```json
{
  "citation_id": "cit_01",
  "node_id": "vbpl:177815:chapter:I:1:article:11:11:clause:1:1",
  "document_id": "177815",
  "document_number": "31/2024/QH15",
  "document_name": "Luat Dat dai 2024",
  "chapter": "I",
  "section": null,
  "article": "11",
  "clause": "1",
  "point": null,
  "display": "Khoan 1 Dieu 11 Luat Dat dai 2024",
  "quote": "Lan dat, chiem dat, huy hoai dat.",
  "source_url": "https://vbpl.vn/...",
  "validity_status": "Con hieu luc",
  "retrieved_at": "2026-07-22T12:00:00Z"
}
```

Quy tac citation:

- `quote` phai la substring cua `content` hoac evidence goc, khong lay tu text do LLM viet lai.
- Citation phai truy vet duoc den `node_id` va `source_url`.
- Neu node la Khoan/Diem, response van phai co ancestor Dieu va Document.
- Neu van ban het hieu luc, citation phai giu `validity_status` de Agent hien thi canh bao.

### 5.4 GraphRelationship

```json
{
  "type": "SUA_DOI",
  "source_id": "vbpl:177815:...:article:11:11",
  "target_id": "vbpl:32833:...:article:12:12",
  "status": "PROPOSED",
  "confidence": 0.93,
  "method": "LLM",
  "model": "gpt-5-nano",
  "similarity_score": 0.89,
  "evidence_source": "...",
  "evidence_target": "...",
  "reason": "..."
}
```

### 5.5 SearchHit

```json
{
  "node": {},
  "score": 0.91,
  "scores": {
    "vector": 0.93,
    "keyword": 0.71,
    "reranker": null,
    "final": 0.91
  },
  "matched_text": "...",
  "citation": {},
  "warnings": []
}
```

Score chi co y nghia xep hang trong cung mot request, khong phai xac suat quy dinh dung.

### 5.6 ErrorResponse

```json
{
  "error": {
    "code": "INVALID_FILTER",
    "message": "levels contains an unsupported value",
    "details": [
      {
        "field": "filters.levels[0]",
        "reason": "allowed: article, clause, point"
      }
    ],
    "request_id": "req_01J...",
    "retryable": false
  }
}
```

## 6. Danh sach endpoint

| Method | Endpoint | Muc dich |
| --- | --- | --- |
| `GET` | `/v1/health` | Kiem tra service va dependency |
| `GET` | `/v1/capabilities` | Kha nang, model va gioi han |
| `GET` | `/v1/graph/schema` | Schema graph cong khai cho Agent |
| `GET` | `/v1/documents` | Liet ke/tim van ban |
| `GET` | `/v1/documents/{document_id}` | Chi tiet van ban |
| `GET` | `/v1/documents/{document_id}/outline` | Cau truc Chuong/Muc/Dieu |
| `POST` | `/v1/legal-nodes:resolve` | Phan giai tham chieu phap ly |
| `GET` | `/v1/legal-nodes/{node_id}` | Lay mot node va citation |
| `POST` | `/v1/legal-nodes:batch-get` | Lay nhieu node |
| `GET` | `/v1/legal-nodes/{node_id}/context` | Lay ancestor/descendant/sibling |
| `POST` | `/v1/search/semantic` | Vector search |
| `POST` | `/v1/search/hybrid` | Vector + keyword search |
| `POST` | `/v1/graph/expand` | Mo rong graph co gioi han |
| `POST` | `/v1/relations/search` | Tim quan he phap ly/ngu nghia |
| `POST` | `/v1/behaviors/search` | Tim hanh vi bi nghiem cam |
| `POST` | `/v1/legal-comparisons/search` | So sanh quy dinh/van ban |
| `POST` | `/v1/retrieval/query` | Graph RAG retrieval cap cao |
| `POST` | `/v1/answers` | Retrieval + sinh cau tra loi |
| `POST` | `/v1/answers:stream` | Cau tra loi SSE |
| `POST` | `/v1/feedback` | Danh gia answer/citation |

## 7. System APIs

### 7.1 `GET /v1/health`

Khong chay truy van nang.

Response `200`:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "dependencies": {
    "neo4j": "ok",
    "embedding_provider": "ok",
    "answer_model": "ok"
  },
  "time": "2026-07-22T12:00:00Z"
}
```

Tra `503` neu Neo4j khong san sang.

### 7.2 `GET /v1/capabilities`

Response `200`:

```json
{
  "retrieval_strategies": ["semantic", "hybrid", "graph", "auto"],
  "supported_levels": ["document", "chapter", "section", "article", "clause", "point"],
  "supported_relationships": [
    "HAS_CHILD",
    "THAY_THE",
    "SUA_DOI",
    "TUONG_UNG",
    "DAN_CHIEU",
    "AP_DUNG_CHUYEN_TIEP",
    "LAM_HET_HIEU_LUC",
    "VI_PHAM"
  ],
  "embedding": {
    "model": "text-embedding-3-small",
    "dimensions": 1536
  },
  "limits": {
    "max_top_k": 50,
    "max_graph_depth": 3,
    "max_context_tokens": 24000
  }
}
```

### 7.3 `GET /v1/graph/schema`

Tra label, property cong khai, quan he va huong. Endpoint nay giup Agent lap ke hoach nhung khong lam lo vector/property noi bo.

Query parameters:

- `include_counts=false`: chi scope `legal:admin` moi duoc dat `true`.

## 8. Document APIs

### 8.1 `GET /v1/documents`

Query parameters:

| Field | Type | Mo ta |
| --- | --- | --- |
| `q` | string | Tu khoa trong so/ten van ban |
| `document_type` | string | Vi du `Luat`, `Nghi dinh` |
| `validity_status` | string | Trang thai hieu luc |
| `issuing_authority` | string | Co quan ban hanh |
| `issued_from`, `issued_to` | date | Khoang ngay ban hanh |
| `limit` | integer | So ban ghi |
| `cursor` | string | Cursor trang tiep theo |

Response la `DocumentSummary[]` kem pagination.

### 8.2 `GET /v1/documents/{document_id}`

Chap nhan `document_id` nghiep vu, vi du `177815`, khong bat client gui `vbpl:177815`.

Query parameters:

- `include_relations=false`
- `relation_status=VERIFIED`

Tra `404 DOCUMENT_NOT_FOUND` neu khong ton tai.

### 8.3 `GET /v1/documents/{document_id}/outline`

Query parameters:

- `depth`: `1..4`, mac dinh `3`.
- `include_content`: mac dinh `false`.

Response:

```json
{
  "document": {},
  "outline": [
    {
      "node": {
        "id": "vbpl:177815:chapter:I:1",
        "level": "chapter",
        "number": "I",
        "title": "Quy dinh chung"
      },
      "children": []
    }
  ],
  "truncated": false
}
```

## 9. Legal node APIs

### 9.1 `POST /v1/legal-nodes:resolve`

Phan giai mot tham chieu nhu "Khoan 1 Dieu 11 Luat Dat dai 2024" thanh stable ID. Day la tool quan trong de Agent khong tu ghep ID phan cap.

Request:

```json
{
  "reference": "Khoan 1 Dieu 11 Luat Dat dai 2024",
  "hints": {
    "document_id": "177815",
    "document_number": "31/2024/QH15"
  },
  "limit": 5
}
```

Response:

```json
{
  "matches": [
    {
      "node": {},
      "citation": {},
      "confidence": 1.0,
      "match_type": "EXACT"
    }
  ],
  "ambiguous": false
}
```

Neu co nhieu van ban cung so Dieu va khong co hint, tra `ambiguous=true`; khong tu chon mot ket qua im lang.

### 9.2 `GET /v1/legal-nodes/{node_id}`

Query parameters:

- `include_ancestors=true`
- `include_children=false`
- `include_relations=false`
- `relation_status=VERIFIED`

Response gom `node`, `ancestors`, `children`, `relations`, `citation` tuy tham so.

`node_id` phai URL encode vi co chua dau `:`.

### 9.3 `POST /v1/legal-nodes:batch-get`

Request:

```json
{
  "ids": ["vbpl:177815:...", "vbpl:32833:..."],
  "include_ancestors": true,
  "include_relations": false
}
```

Toi da 100 ID. Response giu thu tu request va tra rieng `not_found`.

### 9.4 `GET /v1/legal-nodes/{node_id}/context`

Query parameters:

| Field | Mac dinh | Mo ta |
| --- | --- | --- |
| `ancestors` | `true` | Document den parent truc tiep |
| `descendant_depth` | `1` | `0..3` |
| `siblings` | `false` | Node cung parent |
| `include_content` | `true` | Tra noi dung node |
| `max_nodes` | `50` | Gioi han ket qua |

Response phai co `truncated` va `omitted_count` neu vuot gioi han.

## 10. Search APIs

### 10.1 Bo loc chung

```json
{
  "document_ids": ["177815"],
  "document_numbers": ["31/2024/QH15"],
  "levels": ["article", "clause", "point"],
  "validity_statuses": ["Con hieu luc"],
  "issued_from": null,
  "issued_to": null
}
```

Filter phai duoc ap dung tai Neo4j hoac trong candidate pool du lon, khong chi loc top-k nho sau cung lam mat ket qua hop le.

### 10.2 `POST /v1/search/semantic`

Request:

```json
{
  "query": "Hanh vi nao bi nghiem cam trong quan ly dat dai?",
  "index": "legal_node_embedding",
  "filters": {
    "levels": ["article", "clause", "point"],
    "validity_statuses": ["Con hieu luc"]
  },
  "top_k": 10,
  "min_score": 0.65,
  "include_ancestors": true
}
```

`index` chi chap nhan allowlist:

- `legal_node_embedding`
- `article_comparison_embedding`
- `behavior_embedding`

Response:

```json
{
  "query": "...",
  "hits": [],
  "meta": {
    "index": "legal_node_embedding",
    "embedding_model": "text-embedding-3-small",
    "candidate_count": 50,
    "latency_ms": 42
  }
}
```

### 10.3 `POST /v1/search/hybrid`

Request:

```json
{
  "query": "boi thuong khi Nha nuoc thu hoi dat",
  "filters": {
    "levels": ["article", "clause", "point"]
  },
  "top_k": 10,
  "candidate_k": 50,
  "weights": {
    "semantic": 0.7,
    "keyword": 0.3
  },
  "rerank": false
}
```

Khuyen nghi ket hop bang Reciprocal Rank Fusion thay vi cong truc tiep cosine score va full-text score do hai score khong cung thang do.

Neu chua co full-text index, tao:

```cypher
CREATE FULLTEXT INDEX legal_node_fulltext IF NOT EXISTS
FOR (n:LegalNode) ON EACH [n.title, n.content, n.document_name, n.document_number];
```

Response giong semantic search nhung co day du `scores`.

## 11. Graph APIs

### 11.1 `POST /v1/graph/expand`

Request:

```json
{
  "seed_ids": [
    "vbpl:177815:chapter:I:1:article:11:11"
  ],
  "relationships": [
    "HAS_CHILD",
    "SUA_DOI",
    "THAY_THE",
    "TUONG_UNG",
    "DAN_CHIEU"
  ],
  "direction": "BOTH",
  "depth": 2,
  "relationship_statuses": ["VERIFIED"],
  "min_confidence": 0.85,
  "max_nodes": 100,
  "include_paths": true
}
```

Gia tri `direction`: `OUTGOING`, `INCOMING`, `BOTH`.

Response:

```json
{
  "nodes": [],
  "relationships": [],
  "paths": [
    {
      "node_ids": ["source", "target"],
      "relationship_types": ["SUA_DOI"],
      "length": 1
    }
  ],
  "truncated": false
}
```

Khong cho phep depth khong gioi han hoac relationship wildcard tu client.

### 11.2 `POST /v1/relations/search`

Request:

```json
{
  "source": {
    "document_ids": ["177815"],
    "node_ids": []
  },
  "target": {
    "document_ids": ["32833"],
    "node_ids": []
  },
  "types": ["THAY_THE", "SUA_DOI", "TUONG_UNG"],
  "statuses": ["VERIFIED", "PROPOSED"],
  "min_confidence": 0.85,
  "limit": 20,
  "cursor": null
}
```

Response phai tra source/target summary, relationship audit properties va citation cho ca hai dau.

### 11.3 `POST /v1/behaviors/search`

Request:

```json
{
  "query": "lan chiem dat",
  "document_ids": ["177815", "32833"],
  "statuses": ["VERIFIED", "PROPOSED"],
  "top_k": 10,
  "min_score": 0.65,
  "include_source": true
}
```

Response:

```json
{
  "hits": [
    {
      "behavior": {
        "id": "hanh_vi:...",
        "canonical_text": "Lan, chiem, huy hoai dat dai",
        "actor": null,
        "action": "lan, chiem, huy hoai",
        "object": "dat dai",
        "condition": null,
        "status": "PROPOSED",
        "confidence": 1.0
      },
      "score": 0.94,
      "source_node": {},
      "citation": {},
      "warnings": ["Quan he PROPOSED chua duoc chuyen gia phap ly phe duyet"]
    }
  ]
}
```

## 12. Legal comparison API

### 12.1 `POST /v1/legal-comparisons/search`

Dung de tim quy dinh tuong ung giua hai van ban. API uu tien quan he da materialize; vector comparison chi la candidate neu khong co quan he.

Request:

```json
{
  "source_document_id": "177815",
  "target_document_id": "32833",
  "source_node_ids": [],
  "query": "quy dinh ve hanh vi bi nghiem cam",
  "relationship_types": ["THAY_THE", "SUA_DOI", "TUONG_UNG"],
  "statuses": ["VERIFIED", "PROPOSED"],
  "include_vector_candidates": true,
  "top_k": 10
}
```

Moi item response co:

- Source provision va citation.
- Target provision va citation.
- Quan he da import neu co.
- `match_origin`: `GRAPH_RELATION` hoac `VECTOR_CANDIDATE`.
- Confidence, evidence, reason va warning.

`VECTOR_CANDIDATE` khong duoc mo ta la quan he sua doi/thay the da duoc xac nhan.

## 13. Graph RAG Retrieval API

### 13.1 `POST /v1/retrieval/query`

Day la endpoint retrieval mac dinh cho Agent. Endpoint tu chon index, tim seed, mo rong context va tao citation.

Request:

```json
{
  "query": "Luat Dat dai 2024 quy dinh the nao ve lan chiem dat va quy dinh nay thay doi gi so voi Luat 2013?",
  "strategy": "auto",
  "filters": {
    "document_ids": ["177815", "32833"],
    "levels": ["article", "clause", "point"]
  },
  "retrieval": {
    "top_k": 12,
    "candidate_k": 50,
    "min_score": 0.6,
    "rerank": false
  },
  "graph": {
    "enabled": true,
    "relationships": [
      "HAS_CHILD",
      "THAY_THE",
      "SUA_DOI",
      "TUONG_UNG",
      "DAN_CHIEU",
      "VI_PHAM"
    ],
    "depth": 1,
    "relationship_statuses": ["VERIFIED", "PROPOSED"],
    "min_confidence": 0.85,
    "max_nodes": 80
  },
  "context": {
    "include_ancestors": true,
    "include_siblings": false,
    "include_full_article": true,
    "token_budget": 12000,
    "deduplicate": true
  },
  "debug": false
}
```

Gia tri `strategy`:

| Strategy | Hanh vi |
| --- | --- |
| `semantic` | Vector retrieval, khong full-text |
| `hybrid` | Vector + full-text + fusion |
| `graph` | Bat dau tu reference/node da resolve va duyet graph |
| `auto` | Query planner tu chon va co the ket hop cac cach tren |

Response:

```json
{
  "retrieval_id": "ret_01J...",
  "query": "...",
  "strategy_used": "hybrid_graph",
  "contexts": [
    {
      "context_id": "ctx_01",
      "node": {},
      "text": "...",
      "score": 0.92,
      "source": "VECTOR_AND_GRAPH",
      "citation_ids": ["cit_01"],
      "relationship_ids": ["rel_01"],
      "warnings": []
    }
  ],
  "citations": [],
  "graph": {
    "nodes": [],
    "relationships": [],
    "paths": []
  },
  "warnings": [
    "Mot so quan he PROPOSED chua duoc chuyen gia phap ly phe duyet"
  ],
  "coverage": {
    "documents": 2,
    "articles": 2,
    "context_tokens": 6340,
    "truncated": false
  },
  "trace": null
}
```

Neu `debug=true` va caller co scope admin, `trace` co the gom:

- Query da chuan hoa.
- Reference da resolve.
- Index da dung.
- So candidate truoc/sau filter.
- Score tung buoc.
- Graph expansion count.
- Context bi loai do trung lap/token budget.
- Latency tung stage.

Khong dua prompt he thong, secret hoac embedding vao trace.

### 13.2 Retrieval pipeline

Thu tu de xuat:

1. Chuan hoa query nhung giu nguyen ban goc de audit.
2. Nhan dien so van ban, Dieu, Khoan, Diem va goi resolver.
3. Chon retrieval strategy.
4. Tao query embedding bang model trung voi vector index.
5. Lay candidate semantic va/hoac keyword.
6. Ap dung filter document, level, validity.
7. Hop nhat va xep hang candidate.
8. Mo rong ancestor de tao citation day du.
9. Mo rong semantic relationship theo allowlist/status/confidence.
10. Gom Khoan/Diem cung Dieu khi `include_full_article=true`.
11. Loai trung theo stable node ID va noi dung.
12. Cat context theo token budget, uu tien evidence va node score cao.
13. Tra context, citation, graph path, warning va trace.

### 13.3 Chinh sach status

- Mac dinh production: chi dung `VERIFIED` de suy ra quan he phap ly.
- Neu request cho phep `PROPOSED`, response phai co warning o item va cap response.
- Khong bao gio truy xuat `REJECTED` cho answer thong thuong.
- Endpoint admin/audit rieng co the xem `REJECTED`, nhung nam ngoai pham vi v1 nay.

## 14. Answer APIs

### 14.1 `POST /v1/answers`

Request:

```json
{
  "question": "Luat Dat dai 2024 cam nhung hanh vi lan chiem dat nao?",
  "messages": [
    {
      "role": "user",
      "content": "Toi muon tim hieu quy dinh ve hanh vi bi cam."
    }
  ],
  "retrieval": {
    "strategy": "auto",
    "filters": {
      "document_ids": ["177815"],
      "levels": ["article", "clause", "point"]
    },
    "top_k": 12,
    "relationship_statuses": ["VERIFIED", "PROPOSED"],
    "context_token_budget": 12000
  },
  "generation": {
    "language": "vi",
    "format": "markdown",
    "temperature": 0.1,
    "max_output_tokens": 1500,
    "require_citations": true,
    "abstain_when_insufficient": true
  },
  "include_retrieval": false
}
```

Chi cho phep `role`: `user`, `assistant`. Khong nhan `system` message tu client thong thuong.

Response:

```json
{
  "answer_id": "ans_01J...",
  "retrieval_id": "ret_01J...",
  "answer": "Theo Khoan 1 Dieu 11 ... [cit_01]",
  "citations": [],
  "claims": [
    {
      "text": "Lan dat, chiem dat va huy hoai dat la hanh vi bi nghiem cam.",
      "citation_ids": ["cit_01"],
      "support": "DIRECT"
    }
  ],
  "confidence": "HIGH",
  "abstained": false,
  "warnings": [
    "Thong tin chi co tinh chat ho tro tra cuu, khong thay the y kien chuyen mon phap ly."
  ],
  "usage": {
    "input_tokens": 7200,
    "output_tokens": 410
  },
  "retrieval": null
}
```

Gia tri `support`:

- `DIRECT`: noi dung co trong trich dan.
- `INFERRED`: suy luan tu nhieu citation/path; phai dien giai ro.
- `UNSUPPORTED`: khong duoc phep xuat hien khi `require_citations=true`.

Gia tri `confidence`: `HIGH`, `MEDIUM`, `LOW`, dua tren coverage va evidence, khong chi dua tren self-score cua LLM.

API phai `abstained=true` neu:

- Khong tim thay citation phu hop.
- Cac citation mau thuan ma khong du can cu phan giai.
- Cau hoi nam ngoai pham vi du lieu.
- Cau tra loi yeu cau ket luan phap ly ca nhan ma graph khong cung cap du su kien.

### 14.2 `POST /v1/answers:stream`

Request giong `/v1/answers`. Response dung `text/event-stream`:

```text
event: retrieval.completed
data: {"retrieval_id":"ret_01J...","citation_count":3}

event: answer.delta
data: {"text":"Theo Khoan 1 Dieu 11"}

event: citation
data: {"citation_id":"cit_01","citation":{}}

event: answer.completed
data: {"answer_id":"ans_01J...","confidence":"HIGH"}
```

Event bat buoc:

- `retrieval.completed`
- `answer.delta`
- `citation`
- `answer.completed`
- `error`

Citation phai duoc gui truoc hoac cung luc voi delta dau tien tham chieu citation do.

## 15. Feedback API

### 15.1 `POST /v1/feedback`

Request:

```json
{
  "answer_id": "ans_01J...",
  "rating": "INCORRECT",
  "categories": ["WRONG_CITATION", "OUTDATED_DOCUMENT"],
  "comment": "Citation khong ho tro ket luan thu hai.",
  "correct_node_ids": ["vbpl:177815:..."]
}
```

`rating`: `HELPFUL`, `PARTIALLY_HELPFUL`, `INCORRECT`.

Feedback khong tu dong thay doi graph production. No duoc dua vao hang doi review/evaluation.

## 16. Agent tool mapping

REST la contract chuan. MCP hoac function calling layer nen expose cac tool sau:

| Tool | REST endpoint | Khi nao dung |
| --- | --- | --- |
| `search_legal_knowledge` | `POST /search/hybrid` | Tim quy dinh ban dau theo cau hoi |
| `retrieve_legal_context` | `POST /retrieval/query` | Tool Graph RAG mac dinh |
| `resolve_legal_reference` | `POST /legal-nodes:resolve` | Cau hoi co Dieu/Khoan/Diem cu the |
| `get_legal_node` | `GET /legal-nodes/{id}` | Kiem chung noi dung mot node |
| `get_document` | `GET /documents/{id}` | Kiem tra metadata va hieu luc |
| `get_document_outline` | `GET /documents/{id}/outline` | Duyet cau truc van ban |
| `expand_legal_graph` | `POST /graph/expand` | Tim quan he xung quanh node |
| `find_legal_relations` | `POST /relations/search` | Tim sua doi/thay the/dan chieu |
| `find_prohibited_behaviors` | `POST /behaviors/search` | Tra cuu hanh vi bi cam |
| `compare_legal_provisions` | `POST /legal-comparisons/search` | So sanh hai doi van ban |
| `answer_legal_question` | `POST /answers` | Can API tu tong hop cau tra loi |

Huong dan Agent:

1. Dung `retrieve_legal_context` cho cau hoi phap luat mo.
2. Dung `resolve_legal_reference` truoc neu nguoi dung neu ro Dieu/Khoan/Diem.
3. Dung `find_legal_relations` hoac `compare_legal_provisions` khi hoi ve thay doi giua cac phien ban.
4. Kiem tra `validity_status`, `status` va `warnings` truoc khi ket luan.
5. Khong tu tao citation hay stable node ID.
6. Khong mo ta `PROPOSED` la da duoc chuyen gia xac minh.
7. Neu API tra `abstained` hoac khong co citation, Agent phai noi khong du du lieu.

Vi du tool schema rut gon:

```json
{
  "name": "retrieve_legal_context",
  "description": "Tim context va citation trong knowledge graph phap luat Viet Nam.",
  "inputSchema": {
    "type": "object",
    "required": ["query"],
    "properties": {
      "query": {"type": "string", "minLength": 3},
      "document_ids": {
        "type": "array",
        "items": {"type": "string"}
      },
      "include_proposed": {"type": "boolean", "default": false},
      "top_k": {"type": "integer", "minimum": 1, "maximum": 50}
    },
    "additionalProperties": false
  }
}
```

## 17. Neo4j implementation notes

### 17.1 Vector query

```cypher
CALL db.index.vector.queryNodes('legal_node_embedding', $candidateK, $embedding)
YIELD node, score
WHERE ($documentIds IS NULL OR node.document_id IN $documentIds)
  AND ($levels IS NULL OR node.level IN $levels)
RETURN node, score
ORDER BY score DESC
LIMIT $topK;
```

Ten index khong duoc noi chuoi truc tiep tu input. Service phai map enum API sang constant noi bo.

### 17.2 Ancestor context

```cypher
MATCH (node:LegalNode {id: $nodeId})
OPTIONAL MATCH path = (ancestor:LegalNode)-[:HAS_CHILD*1..4]->(node)
RETURN node, nodes(path) AS hierarchy
ORDER BY length(path) DESC;
```

### 17.3 Semantic relations

```cypher
MATCH (source:LegalNode {id: $nodeId})-[r]->(target)
WHERE type(r) IN $relationshipTypes
  AND (r.status IS NULL OR r.status IN $statuses)
  AND (r.confidence IS NULL OR r.confidence >= $minConfidence)
RETURN source, r, target
LIMIT $limit;
```

Trong code thuc te, relationship allowlist nen duoc materialize thanh cac nhanh query co type co dinh de toi uu planner va tranh injection.

### 17.4 Citation builder

Citation builder can:

1. Lay node ket qua.
2. Duyet nguoc `HAS_CHILD` den `Document`.
3. Lay node `Article`, `Clause`, `Point` tren cung path.
4. Dung `content` cua node/evidence lam quote.
5. Dung metadata `Document` lam so van ban, ten, URL va trang thai hieu luc.

Khong dung `embedding_text` de trich dan vi field nay ghep noi ancestor va co the lap noi dung.

## 18. Security va safety

- Chi dung parameterized Cypher.
- Label, relationship, index va sort field phai qua allowlist.
- Gioi han kich thuoc request va do dai query.
- Timeout tat ca Neo4j transaction va LLM request.
- Tach credential Neo4j read-only cho Retrieval Service neu co the.
- Khong log API key, bearer token, raw embedding hoac noi dung hoi thoai nhay cam.
- Ma hoa traffic den Neo4j remote bang `neo4j+s://` hoac `bolt+s://`.
- Them rate limit rieng cho `/answers` vi co chi phi LLM.
- Chong prompt injection: context lay tu graph la du lieu, khong phai chi dan he thong.
- Answer prompt phai yeu cau chi dung evidence da cap va bo qua chi dan nam trong tai lieu nguon.
- Moi response Answer luon co disclaimer tra cuu phap ly.

## 19. Error codes

| HTTP | Code | Mo ta |
| ---: | --- | --- |
| `400` | `INVALID_REQUEST` | JSON/request khong hop le |
| `400` | `INVALID_FILTER` | Filter ngoai allowlist |
| `401` | `UNAUTHENTICATED` | Thieu/sai credential |
| `403` | `FORBIDDEN` | Thieu scope |
| `404` | `DOCUMENT_NOT_FOUND` | Khong tim thay van ban |
| `404` | `LEGAL_NODE_NOT_FOUND` | Khong tim thay node |
| `409` | `EMBEDDING_MODEL_MISMATCH` | Model/dimension khong khop index |
| `422` | `AMBIGUOUS_REFERENCE` | Tham chieu phap ly co nhieu ket qua |
| `422` | `INSUFFICIENT_EVIDENCE` | Khong du evidence de answer |
| `429` | `RATE_LIMITED` | Vuot rate limit |
| `503` | `NEO4J_UNAVAILABLE` | Neo4j khong san sang |
| `503` | `MODEL_UNAVAILABLE` | Embedding/answer provider loi |
| `504` | `RETRIEVAL_TIMEOUT` | Retrieval vuot timeout |

Loi `429`, `503`, `504` nen tra `Retry-After` khi biet thoi gian retry.

## 20. Observability

Moi request can co:

- `request_id`
- `retrieval_id` cho retrieval
- `answer_id` cho answer
- Endpoint/status/latency
- Neo4j query count va time
- Candidate count va context count
- Graph node/relationship count
- Input/output token usage
- Error code

Khong dua full query cua nguoi dung vao metric label. Neu can log de debug, phai co chinh sach retention va redaction.

Metrics de xuat:

- `retrieval_latency_ms`
- `neo4j_query_latency_ms`
- `retrieval_empty_rate`
- `citation_count`
- `context_truncated_rate`
- `answer_abstain_rate`
- `proposed_relation_usage_rate`
- `embedding_provider_error_rate`

## 21. Cache

- Cache embedding theo hash cua normalized query + model + dimensions.
- Cache document metadata va outline ngan han.
- Cache retrieval theo query, filter, graph config va graph version.
- Khong cache Answer co du lieu nguoi dung nhay cam neu chua co chinh sach.
- Invalidate cache khi `extraction_manifest.json`, embedding model hoac graph import version thay doi.

Response co the tra:

```http
Cache-Control: private, max-age=60
ETag: "graph-version:request-hash"
```

## 22. Kiem thu chap nhan

Can co it nhat cac nhom test:

1. Resolve dung Document/Dieu/Khoan/Diem va xu ly tham chieu mo ho.
2. Vector search tra dung label va ap dung filter.
3. Hybrid search khong mat ket qua exact keyword.
4. Graph expansion khong vuot depth/max nodes.
5. `PROPOSED` luon sinh warning.
6. Citation quote ton tai trong noi dung goc.
7. Van ban het hieu luc duoc danh dau trong citation/answer.
8. Answer khong co claim khong citation khi `require_citations=true`.
9. Answer abstain khi retrieval rong.
10. Injection qua index, relationship, sort field bi tu choi.
11. Embedding model/dimensions khong khop index sinh loi ro rang.
12. SSE ket thuc bang `answer.completed` hoac `error`.

## 23. Thu tu trien khai de xuat

1. System, Document, Legal node va resolver APIs.
2. Semantic search va citation builder.
3. Graph expansion, relations va behavior search.
4. Hybrid search + full-text index.
5. `/retrieval/query` va retrieval trace.
6. `/answers` va `/answers:stream`.
7. Agent/MCP adapter, feedback va evaluation dashboard.

MVP cho Agent co the bat dau voi bon tool: `resolve_legal_reference`, `get_legal_node`, `retrieve_legal_context` va `answer_legal_question`.
