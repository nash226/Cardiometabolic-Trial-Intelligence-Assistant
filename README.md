# MTIA: Metabolic Trial Intelligence Assistant

MTIA is a source-grounded clinical trial intelligence assistant for cardiometabolic trial review. It helps users search a curated ClinicalTrials.gov-derived corpus, inspect trial detail pages, and ask evidence-backed questions with citations.

The current app is a Dockerized FastAPI, Postgres, pgvector, and Redis project with a focused server-rendered reviewer UI. The Docker database seeds a small accepted demo corpus so the search, trial detail, and citation flows work immediately.

## What It Demonstrates

- FastAPI retrieval API with typed request and response schemas.
- Postgres-backed lexical search over trial evidence chunks.
- Optional OpenAI-powered semantic and fused retrieval.
- Source-grounded answer generation with extractive fallback.
- Trial detail pages with structured fields and evidence context.
- Seeded reviewer corpus for immediate Docker demos.
- Dockerized API, Postgres + pgvector, and Redis services.

## Demo Scope

The reviewer corpus focuses on cardiometabolic studies, especially:

- Obesity and overweight.
- Type 2 diabetes and GLP-1-related therapy signals.
- Interventional trials relevant to 2026 milestones.
- Evidence snippets that support search and answer flows.

The homepage is intentionally a focused trial-review work surface: a query box, `Search trials`, `Ask with evidence`, matched trial cards, and answer/evidence panels. The old generated query chips under the search box were intentionally removed.

## Tech Stack

- Python 3.12
- FastAPI
- Uvicorn
- Jinja templates
- PostgreSQL
- pgvector
- Redis
- RQ
- OpenAI SDK, optional
- Docker Compose

## Quick Start With Docker

From this project directory:

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8000
```

Docker services:

| Service | Purpose | Host port |
| --- | --- | --- |
| `api` | FastAPI app | `8000` |
| `db` | PostgreSQL + pgvector | `5435` |
| `redis` | Redis queue backend | `6380` |

Database migrations run from `apps/api/db/migrations/` when the Postgres volume is first created.

## Reviewer Workflow

Start at `/` and try:

- `obesity body weight phase 3`
- `semaglutide biomarkers`
- `GLP1 cardiovascular biomarkers`
- `Which phase 3 obesity trials in 2026 involve GLP-1 related therapy?`

Then:

1. Run `Search trials`.
2. Open a result card's trial detail page.
3. Use the trial-specific ask panel on the detail page.
4. Return to the homepage and try `Ask with evidence`.

Without `OPENAI_API_KEY`, the app still returns lexical evidence and extractive fallback answers. With `OPENAI_API_KEY`, semantic and model-backed paths can be enabled.

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Reviewer UI |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/search` | Lexical search |
| `POST` | `/api/v1/search/semantic` | Semantic search |
| `POST` | `/api/v1/search/fused` | Hybrid retrieval |
| `POST` | `/api/v1/ask` | Grounded answer generation |
| `GET` | `/api/v1/trials/{nct_id}` | Trial detail JSON |
| `GET` | `/trials/{nct_id}` | Trial detail page |
| `POST` | `/api/v1/ingestion/jobs` | Queue ingestion job |
| `GET` | `/api/v1/ingestion/jobs` | List ingestion jobs |

## Optional OpenAI Configuration

The app runs without OpenAI credentials. To enable semantic retrieval and model-written synthesis, set:

```bash
OPENAI_API_KEY=your_key_here
```

The reviewer UI is designed to degrade gracefully when this is absent.

## Local Development Without Docker

Use Docker for the recommended reviewer path. For local API development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://mtia:mtia@localhost:5435/mtia
export REDIS_URL=redis://localhost:6380/0
uvicorn apps.api.app.main:app --reload
```

You will need a running Postgres + pgvector database and Redis instance.

## Reset Seed Data

If the reviewer corpus looks stale or you want a clean database:

```bash
docker compose down -v
docker compose up -d --build
```

This removes the Postgres volume and reruns the migrations and demo seed.

## Smoke Checks

Homepage:

```bash
curl -i http://localhost:8000/
curl -sS http://localhost:8000/health
```

Search API:

```bash
curl -sS -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"Which phase 3 obesity trials in 2026 involve GLP-1 related therapy?","accepted_only":true,"year_2026_only":true,"limit":3}'
```

Trial detail:

```bash
curl -sS http://localhost:8000/api/v1/trials/NCT06893016
```

## Project Structure

```text
MTIA---Metabolic-Trial-Intelligence-Assistant/
|-- apps/api/app/main.py          # FastAPI routes
|-- apps/api/app/schemas/         # Pydantic request and response models
|-- apps/api/app/services/        # Search, ask, ingestion, trial detail services
|-- apps/api/app/templates/       # Server-rendered reviewer UI
|-- apps/api/db/migrations/       # Schema and demo seed migrations
|-- scripts/                      # Ingestion, normalization, chunking, search utilities
|-- docs/                         # Architecture and pipeline notes
|-- Dockerfile
|-- docker-compose.yml
|-- .dockerignore
|-- AGENTS.md                     # Agent/reviewer handoff instructions
`-- README.md
```

## Design and Review Notes

- Keep reviewer-facing UI work in `apps/api/app/templates/` unless API behavior must change.
- Keep ingestion and database migrations idempotent.
- Do not re-add the removed query chips under the homepage search form unless explicitly requested.
- Do not commit secrets or local `.env` files.
