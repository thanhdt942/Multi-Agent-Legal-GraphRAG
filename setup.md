# Setup Neo4j và import dữ liệu

Các lệnh dưới đây được chạy từ thư mục gốc chứa hai thư mục `artifacts/` và `scripts/`.

## 1. Đi tới thư mục dự án

```bash
cd "/home/tanthanh/Documents/Projects/Multi-Agent Legal GraphRAG"
```

## 2. Kiểm tra và chuẩn bị migration artifacts

Nếu artifacts đã được chuẩn bị và không thay đổi thì có thể bỏ qua bước này.

```bash
uv run python scripts/prepare_migration_data.py
```

Chỉ tiếp tục sau khi script báo `[ready]`.

## 3. Tạo Python virtual environment

```bash
uv venv
```

## 4. Cài dependencies

```bash
uv pip install -r scripts/requirements-migration.txt
```

## 5. Cấu hình Neo4j

Repository này đã có `.env` ở thư mục gốc. Kiểm tra file:

```bash
nano .env
```

Cập nhật các biến sau và thay `your-strong-password` bằng mật khẩu thực tế:

```dotenv
NEO4J_AUTH=neo4j/your-strong-password
NEO4J_URI=bolt://localhost:7687
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
```

Nếu chạy migration bundle độc lập và chưa có `.env` ở root, tạo file từ mẫu:

```bash
cp scripts/.env.example .env
```

Xóa các biến Neo4j cũ đã export trong shell để `.env` không bị ghi đè:

```bash
unset NEO4J_AUTH NEO4J_URI NEO4J_HTTP_PORT NEO4J_BOLT_PORT
```

## 6. Khởi động Neo4j

```bash
docker compose \
  --env-file .env \
  -f scripts/docker-compose.migration.yml \
  up -d
```

## 7. Kiểm tra trạng thái Neo4j

```bash
docker compose \
  --env-file .env \
  -f scripts/docker-compose.migration.yml \
  ps
```

Địa chỉ mặc định:

- Neo4j Browser: `http://localhost:7474`
- Bolt: `bolt://localhost:7687`
- Username: `neo4j`
- Password: mật khẩu đã đặt trong `NEO4J_AUTH`

## 8. Import toàn bộ dữ liệu

Với database mới hoặc database được phép xóa toàn bộ dữ liệu:

```bash
uv run python scripts/rebuild_neo4j.py --clear
```

> Cảnh báo: `--clear` chạy `MATCH (n) DETACH DELETE n` và xóa toàn bộ dữ liệu hiện có trong database đích.

Nếu database đang chứa dữ liệu cần giữ, không dùng `--clear`:

```bash
uv run python scripts/rebuild_neo4j.py
```

## 9. Import thủ công từng bước khi cần chẩn đoán lỗi

Không cần chạy phần này nếu bước 8 đã thành công. Luôn chạy hai lệnh theo đúng thứ tự:

```bash
uv run python scripts/import_neo4j.py
uv run python scripts/import_artifacts.py
```

## 10. Kiểm tra dữ liệu sau import

Mở Neo4j Browser tại `http://localhost:7474` và chạy các truy vấn sau.

### Số lượng node theo label

```cypher
MATCH (n)
UNWIND labels(n) AS label
RETURN label, count(*) AS count
ORDER BY count DESC;
```

### Số lượng relationship

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS count
ORDER BY relationship;
```

### Trạng thái vector indexes

```cypher
SHOW VECTOR INDEXES
YIELD name, state, populationPercent, labelsOrTypes, properties
RETURN name, state, populationPercent, labelsOrTypes, properties;
```

Ba index sau phải chuyển sang trạng thái `ONLINE`:

```text
legal_node_embedding
article_comparison_embedding
behavior_embedding
```

### Kiểm tra kích thước embedding

```cypher
MATCH (n:LegalNode)
RETURN count(n) AS total,
       count(n.embedding) AS embedded,
       min(size(n.embedding)) AS min_dimensions,
       max(size(n.embedding)) AS max_dimensions;
```

`min_dimensions` và `max_dimensions` phải bằng `1536` với bundle hiện tại.

## Chuỗi lệnh chính

Sau khi đã cập nhật `.env`, quy trình chính là:

```bash
uv venv
uv pip install -r scripts/requirements-migration.txt
unset NEO4J_AUTH NEO4J_URI NEO4J_HTTP_PORT NEO4J_BOLT_PORT
docker compose --env-file .env -f scripts/docker-compose.migration.yml up -d
docker compose --env-file .env -f scripts/docker-compose.migration.yml ps
uv run python scripts/rebuild_neo4j.py --clear
```
