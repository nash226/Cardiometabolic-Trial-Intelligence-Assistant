# MTIA Agent Notes

MTIA is a FastAPI/Postgres/pgvector clinical trial intelligence assistant for source-grounded trial search and question answering.

## Run The App

Use Docker for the reviewer path:

```bash
docker compose up -d --build
```

Open `http://localhost:8000`.

Docker services:

- `api`: FastAPI app on host port `8000`
- `db`: Postgres + pgvector on host port `5435`
- `redis`: Redis on host port `6380`

The Docker database runs migrations from `apps/api/db/migrations/` and seeds a small accepted demo corpus so search, trial detail, and citation flows work immediately. Seed data loads when the Docker volume is first created. If data looks stale during review, reset with:

```bash
docker compose down -v
docker compose up -d --build
```

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://mtia:mtia@localhost:5435/mtia
uvicorn apps.api.app.main:app --reload
```

Optional:

- `OPENAI_API_KEY` enables semantic retrieval and model-written synthesis.
- Without `OPENAI_API_KEY`, fused search falls back to lexical evidence and answer generation returns an extractive citation summary.

## Reviewer Workflow

Start at `/`, try searches such as:

- `obesity body weight phase 3`
- `semaglutide biomarkers`
- `GLP1 cardiovascular biomarkers`

Open a trial detail page from the result cards and use the trial-specific ask panel.

Reviewer smoke checks:

```bash
curl -sS http://localhost:8000/ >/tmp/mtia-home.html
curl -sS -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"Which phase 3 obesity trials in 2026 involve GLP-1 related therapy?","accepted_only":true,"year_2026_only":true,"limit":3}'
```

## Current UI Direction

The homepage is intentionally a focused trial-review work surface: query box, `Search trials`, `Ask with evidence`, matched trials, and answer/evidence panels. The old generated query chips under the search form were intentionally removed. Do not re-add `accepted corpus`, `2026 relevant`, `phase 3`, `obesity`, or `GLP-1` chips under the query box unless Nazeer explicitly asks.

## Boundaries

Keep reviewer-facing UI work in `apps/api/app/templates/` unless endpoint behavior must change. Keep ingestion and database changes idempotent because migrations may be rerun locally. Do not commit secrets. Do not revert unrelated work.
