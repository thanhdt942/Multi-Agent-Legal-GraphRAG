# Hướng dẫn chuyển dữ liệu sang Neo4j khác

## 1. Mục tiêu

Migration bundle của dự án được tổ chức thành đúng hai thư mục:

```text
artifacts/   # Toàn bộ dữ liệu và cache cần để khôi phục graph
scripts/     # Script import, cấu hình Docker và dependency
```

Sau khi chuẩn bị bundle, chỉ cần copy hai thư mục này sang dự án hoặc máy khác. Không cần copy `.env`, volume `neo4j/`, HTML nguồn, virtual environment hoặc toàn bộ repository.

Đường import được khuyến nghị không gọi OpenAI. Nó dùng vector, quan hệ và hành vi đã lưu trong `artifacts/`.

## 2. Cấu trúc bundle

### 2.1 Thư mục dữ liệu `artifacts/`

Các file bắt buộc để import graph hoàn chỉnh:

```text
artifacts/
├── flatten.jsonl
├── relationship.parquet
├── extracted_relations.jsonl
├── extracted_behaviors.jsonl
├── legal_node_embeddings.parquet
├── article_comparison_embeddings.parquet
└── behavior_embeddings.parquet
```

Ý nghĩa:

| File | Mục đích |
| --- | --- |
| `flatten.jsonl` | Node `Document`, `Chapter`, `Section`, `Article`, `Clause`, `Point` và cấu trúc cha-con |
| `relationship.parquet` | Quan hệ gốc giữa các `Document` |
| `extracted_relations.jsonl` | Quan hệ `THAY_THE`, `SUA_DOI`, `TUONG_UNG`, `DAN_CHIEU`, `AP_DUNG_CHUYEN_TIEP`, `LAM_HET_HIEU_LUC` |
| `extracted_behaviors.jsonl` | Node `HanhVi` và quan hệ `VI_PHAM` |
| `legal_node_embeddings.parquet` | Vector của toàn bộ `LegalNode` |
| `article_comparison_embeddings.parquet` | Vector dùng để so sánh `Article` |
| `behavior_embeddings.parquet` | Vector của `HanhVi` |

Các file nên giữ để audit hoặc tái tạo pipeline:

```text
artifacts/
├── parsed.json
├── extraction_manifest.json
├── migration_manifest.json
├── article_candidates.jsonl
├── llm_article_results.jsonl
├── llm_behavior_results.jsonl
├── import.cypher
└── import_extracted_relations.cypher
```

Trong đó:

- `parsed.json` chỉ cần khi muốn chạy lại `build_flatten.py`.
- Các file `llm_*.jsonl` là cache, giúp chạy lại extraction mà không gọi lại LLM nếu input không đổi.
- `migration_manifest.json` chứa kích thước và SHA-256 của các file bắt buộc để kiểm tra dữ liệu sau khi copy.
- Hai file Cypher không được dùng trong đường import Python mặc định.

### 2.2 Thư mục `scripts/`

Các file cần cho migration tối thiểu:

```text
scripts/
├── rebuild_neo4j.py
├── import_neo4j.py
├── import_artifacts.py
├── neo4j_client.py
├── rel_normalizer.py
├── prepare_migration_data.py
├── requirements-migration.txt
├── docker-compose.migration.yml
└── .env.example
```

Các script còn lại cho phép tái tạo toàn bộ pipeline:

```text
scripts/
├── build_flatten.py
├── embed_neo4j.py
├── extract_legal_relations.py
└── extract_behaviors.py
```

## 3. Chuẩn bị bundle ở dự án nguồn

Chạy từ thư mục gốc của dự án nguồn:

```bash
uv run python scripts/prepare_migration_data.py
```

Script thực hiện các việc sau:

1. Kiểm tra sáu artifact cấu trúc, semantic và vector bắt buộc.
2. Copy `relationship.parquet` vào `artifacts/relationship.parquet`.
3. Copy `parsed.json` vào `artifacts/parsed.json` để có thể tái tạo pipeline.
4. Tạo `artifacts/migration_manifest.json` với kích thước và SHA-256.

Sau khi script báo `[ready]`, bundle cần copy chỉ còn:

```text
artifacts/
scripts/
```

Không sửa trực tiếp vector Parquet hoặc JSONL sau khi tạo manifest. Nếu dữ liệu thay đổi, chạy lại `prepare_migration_data.py` để cập nhật manifest.

## 4. Copy sang dự án hoặc máy khác

Ví dụ cấu trúc tại máy đích:

```text
legal-graph-migration/
├── artifacts/
└── scripts/
```

Có thể copy qua `rsync`:

```bash
rsync -av --progress artifacts/ user@target:/opt/legal-graph-migration/artifacts/
rsync -av --progress scripts/ user@target:/opt/legal-graph-migration/scripts/
```

Hoặc đóng gói hai thư mục:

```bash
tar -czf legal-graph-migration.tar.gz artifacts scripts
```

Tại máy đích:

```bash
mkdir -p /opt/legal-graph-migration
tar -xzf legal-graph-migration.tar.gz -C /opt/legal-graph-migration
```

Không đóng gói `.env` có secret thật.

## 5. Yêu cầu máy đích

- Python 3.13 trở lên được khuyến nghị.
- Neo4j 5.26 trở lên để hỗ trợ vector index được sử dụng trong dự án.
- Docker Engine và Docker Compose nếu muốn chạy Neo4j local bằng cấu hình đi kèm.
- Đủ dung lượng cho artifact và database sau import.
- Kết nối Bolt từ máy chạy script đến Neo4j đích.

Neo4j Community đủ để chạy graph hiện tại.

## 6. Cài môi trường Python

### 6.1 Dùng `uv`

Chạy trong thư mục chứa `artifacts/` và `scripts/`:

```bash
uv venv
uv pip install -r scripts/requirements-migration.txt
```

Sau đó dùng:

```bash
uv run python scripts/rebuild_neo4j.py
```

### 6.2 Dùng Python `venv` và `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements-migration.txt
```

Sau đó dùng:

```bash
python scripts/rebuild_neo4j.py
```

## 7. Tạo cấu hình kết nối

Tạo file cấu hình nằm ngay trong thư mục `scripts/`:

```bash
cp scripts/.env.example scripts/.env
```

Nội dung tối thiểu:

```dotenv
NEO4J_AUTH=neo4j/your-strong-password
NEO4J_URI=bolt://localhost:7687
```

Các script hỗ trợ cả hai vị trí:

- `.env` tại thư mục gốc, dùng trong repository phát triển.
- `scripts/.env`, dùng cho migration bundle hai thư mục.

Không commit hoặc gửi `scripts/.env` có mật khẩu thật.

## 8. Phương án A: tạo Neo4j local mới bằng Docker

### 8.1 Khởi động database

Sửa mật khẩu trong `scripts/.env`, sau đó chạy:

```bash
docker compose \
  --env-file scripts/.env \
  -f scripts/docker-compose.migration.yml \
  up -d
```

Kiểm tra:

```bash
docker compose \
  --env-file scripts/.env \
  -f scripts/docker-compose.migration.yml \
  ps
```

Địa chỉ mặc định:

- Neo4j Browser: `http://localhost:7474`
- Bolt: `bolt://localhost:7687`

Compose sử dụng named volume, vì vậy dữ liệu database không nằm lẫn trong `scripts/` hoặc `artifacts/`.

Nếu port đã được sử dụng, sửa trong `scripts/.env`:

```dotenv
NEO4J_HTTP_PORT=17474
NEO4J_BOLT_PORT=17687
NEO4J_URI=bolt://localhost:17687
```

### 8.2 Import graph

Với database mới, chạy:

```bash
uv run python scripts/rebuild_neo4j.py --clear
```

Hoặc khi dùng virtual environment thông thường:

```bash
python scripts/rebuild_neo4j.py --clear
```

`rebuild_neo4j.py` chạy theo thứ tự:

1. Kiểm tra artifact bắt buộc.
2. Nếu có `--clear`, chạy `MATCH (n) DETACH DELETE n`.
3. Chạy `import_neo4j.py` để import node cấu trúc, `HAS_CHILD` và quan hệ Document.
4. Chạy `import_artifacts.py` để import semantic relations, `HanhVi`, vector và vector index.

Quá trình này không gọi OpenAI.

## 9. Phương án B: import vào Neo4j remote hoặc Neo4j đã có sẵn

Không cần chạy Docker Compose. Cấu hình `scripts/.env` theo database đích:

```dotenv
NEO4J_AUTH=neo4j/your-remote-password
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
```

Hoặc với server nội bộ có TLS:

```dotenv
NEO4J_URI=bolt+s://neo4j.example.internal:7687
```

Kiểm tra kỹ database đích trước khi chạy.

### 9.1 Database đích dành riêng cho graph này

```bash
uv run python scripts/rebuild_neo4j.py --clear
```

### 9.2 Database đích đang chứa dữ liệu khác

Không dùng `--clear`:

```bash
uv run python scripts/rebuild_neo4j.py
```

Lưu ý khi không dùng `--clear`:

- Node được `MERGE` theo stable ID nên node trùng sẽ được cập nhật.
- `HAS_CHILD` và quan hệ Document được `MERGE`.
- `import_artifacts.py` xóa các quan hệ semantic cũ có `method` là `RULE` hoặc `LLM`, sau đó import lại từ artifact.
- `import_artifacts.py` xóa và tạo lại toàn bộ node `HanhVi`.
- Node cấu trúc cũ không còn xuất hiện trong bundle sẽ không tự bị xóa.

Nếu database dùng chung có semantic relation hoặc `HanhVi` của ứng dụng khác, không chạy trực tiếp pipeline hiện tại. Nên dùng database riêng hoặc bổ sung tenant/dataset ID trước.

## 10. Import từng bước

Nếu cần chẩn đoán lỗi, có thể chạy riêng:

```bash
# Cấu trúc pháp luật và quan hệ giữa Document
uv run python scripts/import_neo4j.py

# Quan hệ semantic, HanhVi, embeddings và vector indexes
uv run python scripts/import_artifacts.py
```

Luôn chạy `import_neo4j.py` trước `import_artifacts.py`, vì semantic relation tham chiếu đến stable ID của `LegalNode`.

## 11. Kiểm tra sau import

Mở Neo4j Browser và chạy các truy vấn sau.

### 11.1 Số lượng node theo label

```cypher
MATCH (n)
UNWIND labels(n) AS label
RETURN label, count(*) AS count
ORDER BY count DESC;
```

Theo manifest hiện tại, graph có khoảng 12.775 `LegalNode` và 21 `HanhVi`. Số liệu có thể thay đổi khi bundle được cập nhật.

### 11.2 Số lượng relationship

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS count
ORDER BY relationship;
```

Phải có `HAS_CHILD`; tùy dữ liệu còn có các quan hệ Document, semantic relation và `VI_PHAM`.

### 11.3 Vector indexes

```cypher
SHOW VECTOR INDEXES
YIELD name, state, populationPercent, labelsOrTypes, properties
RETURN name, state, populationPercent, labelsOrTypes, properties;
```

Các index cần có:

```text
legal_node_embedding
article_comparison_embedding
behavior_embedding
```

Chờ đến khi `state = 'ONLINE'` trước khi chạy Graph RAG.

### 11.4 Coverage embedding

```cypher
MATCH (n:LegalNode)
RETURN count(n) AS total,
       count(n.embedding) AS embedded,
       min(size(n.embedding)) AS min_dimensions,
       max(size(n.embedding)) AS max_dimensions;
```

`min_dimensions` và `max_dimensions` phải bằng `1536` với bundle hiện tại.

Kiểm tra `Article`:

```cypher
MATCH (n:Article)
RETURN count(n) AS total,
       count(n.comparison_embedding) AS embedded,
       min(size(n.comparison_embedding)) AS min_dimensions,
       max(size(n.comparison_embedding)) AS max_dimensions;
```

### 11.5 Vector search thử nghiệm

Vector search yêu cầu query vector 1.536 chiều được tạo bằng cùng embedding model. Có thể kiểm tra index bằng cách dùng vector của một node đã import:

```cypher
MATCH (seed:LegalNode)
WHERE seed.embedding IS NOT NULL
WITH seed LIMIT 1
CALL db.index.vector.queryNodes('legal_node_embedding', 5, seed.embedding)
YIELD node, score
RETURN seed.id AS seed_id, node.id, node.level, node.title, score
ORDER BY score DESC;
```

## 12. Kiểm tra tính toàn vẹn file

`artifacts/migration_manifest.json` lưu SHA-256 và kích thước của các file quan trọng. Chạy lại script ở máy đích không làm thay đổi dữ liệu; nó sẽ kiểm tra file và tạo lại manifest:

```bash
uv run python scripts/prepare_migration_data.py
```

Vì `parsed.json` và `relationship.parquet` đã nằm trong `artifacts/`, script không cần các file ở thư mục gốc trên máy đích.

Để so sánh chính xác với manifest nguồn, nên lưu một bản manifest trước khi chạy lại hoặc dùng công cụ SHA-256 của hệ điều hành:

```bash
sha256sum artifacts/flatten.jsonl
sha256sum artifacts/relationship.parquet
sha256sum artifacts/legal_node_embeddings.parquet
```

## 13. Tái tạo toàn bộ pipeline tại máy đích

Chỉ thực hiện phần này khi muốn thay đổi dữ liệu, embedding model hoặc chạy extraction mới.

### 13.1 Cấu hình OpenAI

Thêm vào `scripts/.env`:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
OPENAI_EXTRACTION_MODEL=gpt-5-nano
ARTICLE_CANDIDATE_TOP_K=3
RELATION_CONFIDENCE_THRESHOLD=0.85
LLM_MAX_WORKERS=10
```

### 13.2 Chạy pipeline

```bash
# Tạo lại flatten.jsonl và import.cypher từ artifacts/parsed.json.
uv run python scripts/build_flatten.py

# Import cấu trúc mới.
uv run python scripts/import_neo4j.py

# Tạo/cập nhật vector; có thể gọi OpenAI.
uv run python scripts/embed_neo4j.py

# Trích xuất quan hệ; có thể gọi OpenAI nếu cache không còn hợp lệ.
uv run python scripts/extract_legal_relations.py

# Trích xuất hành vi; có thể gọi OpenAI nếu cache không còn hợp lệ.
uv run python scripts/extract_behaviors.py

# Import semantic data, vector và tạo index.
uv run python scripts/import_artifacts.py

# Cập nhật manifest migration sau khi artifact thay đổi.
uv run python scripts/prepare_migration_data.py
```

Không đổi embedding dimensions nếu chưa chủ động tái tạo toàn bộ vector và vector index.

## 14. File và thư mục không cần copy

Không cần copy các thành phần sau để import graph:

| Thành phần | Lý do |
| --- | --- |
| `.env` hoặc `scripts/.env` nguồn | Có secret; phải tạo mới tại máy đích |
| `.venv/` | Phụ thuộc hệ điều hành và Python tại máy nguồn |
| `neo4j/data/` | Volume database cũ; import từ artifact an toàn và dễ kiểm soát hơn |
| `neo4j/logs/` | Chỉ là log runtime |
| `neo4j/plugins/` | Đường import Python không cần APOC |
| `html/` | Không được dùng trong quá trình import hiện tại |
| `main.ipynb`, `main.py` | Không tham gia pipeline import |
| `.git/` | Không cần cho migration runtime |

Không nên copy trực tiếp `neo4j/data/` giữa các phiên bản Neo4j hoặc hệ điều hành khác. Nếu bắt buộc chuyển database vật lý, phải dùng quy trình dump/load chính thức của Neo4j; đó là phương án khác với artifact import trong tài liệu này.

## 15. APOC có cần thiết không?

Đường chạy được khuyến nghị:

```bash
uv run python scripts/rebuild_neo4j.py --clear
```

không cần APOC vì dữ liệu được gửi qua Neo4j Python driver bằng parameterized Cypher.

APOC chỉ cần nếu chọn chạy thủ công `artifacts/import_extracted_relations.cypher`, do file này dùng `apoc.convert.fromJsonMap`. Không nên dùng đường Cypher thủ công khi đã có các Parquet vector và script Python đầy đủ.

## 16. Xử lý lỗi thường gặp

### Thiếu artifact

Lỗi:

```text
Missing required artifacts: [...]
```

Cách xử lý: kiểm tra danh sách file bắt buộc trong `artifacts/`, sau đó chạy lại `prepare_migration_data.py` ở nguồn và copy lại thư mục.

### Không kết nối được Neo4j

Kiểm tra:

```bash
docker compose \
  --env-file scripts/.env \
  -f scripts/docker-compose.migration.yml \
  ps
```

Kiểm tra `NEO4J_URI`, firewall và port Bolt.

### Sai mật khẩu

`NEO4J_AUTH` trong Compose chỉ thiết lập mật khẩu khi volume Neo4j được tạo lần đầu. Sửa `.env` không tự đổi mật khẩu của named volume đã tồn tại.

Với môi trường thử nghiệm chưa có dữ liệu cần giữ, có thể dừng và xóa volume rồi tạo lại:

```bash
docker compose \
  --env-file scripts/.env \
  -f scripts/docker-compose.migration.yml \
  down -v
```

Lệnh này xóa database local của bundle. Không chạy nếu volume chứa dữ liệu cần giữ.

### Vector index không `ONLINE`

Chờ index populate và kiểm tra lại `SHOW VECTOR INDEXES`. Nếu index báo lỗi dimension, xác nhận tất cả vector có 1.536 phần tử và `OPENAI_EMBEDDING_DIMENSIONS=1536`.

### Có node cũ sau import

Nguyên nhân thường là chạy không có `--clear` trên database đã từng chứa phiên bản bundle khác. Với database dành riêng và có thể xóa, chạy lại:

```bash
uv run python scripts/rebuild_neo4j.py --clear
```

### Import semantic không tìm thấy source/target

Đảm bảo `import_neo4j.py` hoàn thành trước `import_artifacts.py`, và `flatten.jsonl` cùng `extracted_*.jsonl` thuộc cùng một bundle/version.

## 17. Checklist migration

- [ ] Đã chạy `scripts/prepare_migration_data.py` tại nguồn.
- [ ] Chỉ copy hai thư mục `artifacts/` và `scripts/`.
- [ ] Không copy file `.env` có secret.
- [ ] Đã cài `scripts/requirements-migration.txt`.
- [ ] Neo4j đích là phiên bản 5.26 trở lên.
- [ ] `scripts/.env` trỏ đúng Neo4j đích.
- [ ] Đã xác nhận có được phép dùng `--clear` hay không.
- [ ] `rebuild_neo4j.py` hoàn thành không lỗi.
- [ ] Số lượng node/relationship hợp lý.
- [ ] Ba vector index ở trạng thái `ONLINE`.
- [ ] Embedding có đúng 1.536 chiều.
- [ ] Vector search thử nghiệm trả kết quả.
- [ ] `PROPOSED` vẫn được ứng dụng hiển thị là dữ liệu cần chuyên gia rà soát.
