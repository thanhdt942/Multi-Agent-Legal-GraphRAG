# Vietnamese Legal Graph Multi-Agent Workbench

Next.js legal research workbench backed by FastAPI, LangGraph, and the existing Neo4j legal graph. The answer workflow routes through situation analysis, graph retrieval, optional Land Law 2024/2013 comparison, answer synthesis, and independent legal criticism.

## Configuration

The service reads the root `.env` without logging secret values:

```dotenv
NEO4J_URI=bolt://localhost:7687
NEO4J_AUTH=neo4j/your-password
OPENAI_API_KEY=your-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
OPENAI_ANSWER_MODEL=gpt-5.4-mini
OPENAI_CRITIC_MODEL=gpt-5.4-mini
AGENT_MAX_CRITIQUE_ATTEMPTS=2
AGENT_CHECKPOINT_PATH=.legal_graph_checkpoints.sqlite
ANSWER_TIMEOUT_MS=60000
```

The embedding model and dimensions must match the imported vector indexes. Startup checks dimensions and safely creates `legal_node_fulltext` with `IF NOT EXISTS`. It does not import, delete, or alter graph data.

## Run Backend

```bash
uv sync --dev
uv run uvicorn legal_graph.main:app --host 0.0.0.0 --port 8000
```

OpenAPI is available at `http://localhost:8000/docs`. All API routes use `/v1`; authentication is intentionally not enabled yet.

## Run Frontend

The Next.js App Router frontend proxies API and SSE requests to FastAPI, so browser CORS configuration is not required.

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The Legal Research Workbench is available at `http://localhost:3000`. Set `API_BASE_URL` in `frontend/.env.local` when FastAPI is not running at `http://127.0.0.1:8000`.

Useful checks:

```bash
curl -s http://localhost:8000/v1/health
curl -s http://localhost:8000/v1/capabilities
curl -s 'http://localhost:8000/v1/documents?limit=2'
```

Semantic, hybrid, behavior, comparison, and high-level retrieval calls use OpenAI embeddings. Answer calls additionally use structured OpenAI generation for situation analysis, synthesis, and legal criticism, and therefore incur API usage.

## Multi-Agent Answers

Use `POST /v1/answers` for a validated final answer:

```bash
curl -X POST http://localhost:8000/v1/answers \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "Luat Dat dai 2024 quy dinh the nao ve lan chiem dat?",
    "thread_id": "land-law-demo",
    "retrieval": {
      "filters": {"document_ids": ["177815"]},
      "top_k": 12
    },
    "include_retrieval": false
  }'
```

Use `POST /v1/answers:stream` with the same request for SSE. It emits agent progress and the required `retrieval.completed`, `citation`, `answer.delta`, `answer.completed`, or `error` events. Citations are emitted before answer text, and answer text is emitted only after the Legal Critic passes it.

The Next.js client under `frontend/` consumes SSE through a server-side Route Handler. It includes responsive research dossiers, dark mode, live agent status, inline citation buttons, an evidence desk with exact quotes, request cancellation, and local browser persistence.

The historical comparison agent is intentionally limited to Land Law 2024 (`177815`) and Land Law 2013 (`32833`). `PROPOSED` and `VECTOR_CANDIDATE` relationships are never presented as verified amendments. Conversation checkpoints persist in the configured SQLite file; clients should provide a stable `thread_id` for follow-up questions.

## Quality Checks

```bash
uv run ruff format --check src tests
uv run ruff check src tests
uv run pytest
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

## Layout

```text
frontend/              # Next.js legal research workbench and SSE proxy
src/legal_graph/
├── agents/            # LangGraph state, prompts, routing, synthesis, critic
├── core/              # settings, errors, request middleware
├── application/       # validated contracts, ports, retrieval services
├── infrastructure/    # async Neo4j and AsyncOpenAI adapters
└── http/v1/           # FastAPI routes and dependency wiring
```

Responses never expose vectors or embedding source text. Citations use the original node `content` and actual `HAS_CHILD` ancestry. `PROPOSED` results carry a review warning; source relationships without imported status preserve `status: null` and carry a `SOURCE_METADATA` warning.
