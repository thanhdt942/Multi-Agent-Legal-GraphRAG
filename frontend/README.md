# Pháp Điển AI Frontend

Next.js App Router frontend for the Legal Graph multi-agent service. The browser talks only to Next.js Route Handlers; `API_BASE_URL` remains server-side and SSE response bodies are forwarded without buffering.

## Configure

```bash
cp .env.example .env.local
```

Default configuration:

```dotenv
API_BASE_URL=http://127.0.0.1:8000
```

## Run

Start FastAPI from the repository root, then run:

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Verify

```bash
npm run lint
npm run typecheck
npm test
npm run build
npm audit --audit-level=moderate
```

The workbench supports live agent progress, abortable SSE, local research dossiers, citation-aware Markdown, exact source quotes, dark mode, and responsive evidence/history drawers.
