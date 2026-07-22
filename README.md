# Vietnamese Legal Graph Retrieval API

FastAPI retrieval service over the existing Neo4j legal graph. It implements the non-answer endpoints from `API design.md` and keeps retrieval use cases independent from HTTP so LangGraph, MCP, or OpenAI Agents SDK adapters can reuse them.

## Configuration

The service reads the root `.env` without logging secret values:

```dotenv
NEO4J_URI=bolt://localhost:7687
NEO4J_AUTH=neo4j/your-password
OPENAI_API_KEY=your-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
```

The embedding model and dimensions must match the imported vector indexes. Startup checks dimensions and safely creates `legal_node_fulltext` with `IF NOT EXISTS`. It does not import, delete, or alter graph data.

## Run

```bash
uv sync --dev
uv run uvicorn legal_graph.main:app --host 0.0.0.0 --port 8000
```

OpenAPI is available at `http://localhost:8000/docs`. All routes use `/v1`; authentication is intentionally not enabled yet.

Useful checks:

```bash
curl -s http://localhost:8000/v1/health
curl -s http://localhost:8000/v1/capabilities
curl -s 'http://localhost:8000/v1/documents?limit=2'
```

Semantic, hybrid, behavior, comparison, and high-level retrieval calls use OpenAI embeddings and therefore incur API usage. Document, node, resolver, schema, graph, and relation calls do not call OpenAI.

## Quality Checks

```bash
uv run ruff format --check src tests
uv run ruff check src tests
uv run pytest
```

## Layout

```text
src/legal_graph/
├── core/             # settings, errors, request middleware
├── application/      # validated contracts, ports, retrieval services
├── infrastructure/   # async Neo4j and AsyncOpenAI adapters
└── http/v1/          # FastAPI routes and dependency wiring
```

Responses never expose vectors or embedding source text. Citations use the original node `content` and actual `HAS_CHILD` ancestry. `PROPOSED` results carry a review warning; source relationships without imported status preserve `status: null` and carry a `SOURCE_METADATA` warning.
