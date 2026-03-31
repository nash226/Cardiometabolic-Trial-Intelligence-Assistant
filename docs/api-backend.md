# API Backend

This is the first backend service layer over the stored trial corpus.

## App entrypoint

- [apps/api/app/main.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/main.py)

## Current endpoint

- `GET /health`
- `POST /api/v1/search`
- `POST /api/v1/search/semantic`
- `POST /api/v1/search/fused`
- `POST /api/v1/ask`
- `GET /api/v1/trials/{nct_id}`

## What `POST /api/v1/search` does

It runs DB-backed structured + lexical retrieval over the stored corpus.

Request body:

```json
{
  "query": "primary completion",
  "condition": "obesity",
  "phase": "PHASE3",
  "study_type": "INTERVENTIONAL",
  "accepted_only": true,
  "year_2026_only": true,
  "limit": 5
}
```

## Run locally

First install dependencies in your venv:

```bash
pip install -r requirements.txt
```

Then start the API:

```bash
uvicorn apps.api.app.main:app --reload
```

If you are using the new template-based frontend pages, make sure the updated Python dependencies are installed first:

```bash
pip install -r requirements.txt
```

## Why this matters

The retrieval system is no longer just a set of scripts.

It now has:

- a backend service boundary
- typed request/response models
- a stable endpoint the frontend can call

## Semantic search endpoint

`POST /api/v1/search/semantic` runs DB-backed semantic retrieval over `trial_chunks.embedding`.

Example request:

```json
{
  "query": "incretin obesity therapy",
  "accepted_only": true,
  "study_type": "INTERVENTIONAL",
  "year_2026_only": true,
  "provider": "openai",
  "model": "text-embedding-3-small",
  "limit": 5
}
```

## Fused search endpoint

`POST /api/v1/search/fused` runs DB-backed fused retrieval. It applies the same structured filters, computes lexical and semantic scores for eligible chunks, normalizes both score streams, applies query-aware chunk-type weighting, and returns a combined ranking with transparent score breakdowns.

For example:

- therapy / intervention questions boost `conditions_interventions`
- timeline / completion questions boost `timeline`
- eligibility questions boost `eligibility`
- endpoint questions boost `outcomes`

Example request:

```json
{
  "query": "incretin obesity therapy",
  "accepted_only": true,
  "study_type": "INTERVENTIONAL",
  "year_2026_only": true,
  "provider": "openai",
  "model": "text-embedding-3-small",
  "lexical_weight": 0.4,
  "semantic_weight": 0.6,
  "limit": 5
}
```

Each fused result now includes:

- `chunk_type_weight`
- `lexical_score_raw`
- `semantic_score_raw`
- `lexical_score_norm`
- `semantic_score_norm`
- `fused_score`

## Ask endpoint

`POST /api/v1/ask` is the first grounded answer-generation layer.

It does this in order:

1. runs fused retrieval over the stored corpus
2. builds a constrained evidence prompt from the returned chunks
3. asks the model to answer only from that evidence
4. returns the answer plus cited chunk metadata

If model synthesis fails, the endpoint falls back to an extractive evidence summary instead of returning an ungrounded answer.

OpenAI integration now uses the official Python SDK:

- embeddings via `client.embeddings.create(...)`
- answer generation via `client.responses.create(...)`

Example request:

```json
{
  "question": "Which 2026 obesity trials appear to involve incretin-related therapy?",
  "accepted_only": true,
  "condition": "obesity",
  "study_type": "INTERVENTIONAL",
  "year_2026_only": true,
  "provider": "openai",
  "embedding_model": "text-embedding-3-small",
  "answer_model": "gpt-4o-mini",
  "lexical_weight": 0.4,
  "semantic_weight": 0.6,
  "retrieval_limit": 5
}
```

## Trial detail endpoint

`GET /api/v1/trials/{nct_id}` returns the stored normalized trial record, child collections, validation state, and chunk previews for one study.

This is the backend contract for:

- result card drill-down
- trial detail page
- compare view preparation

Example:

```bash
curl http://127.0.0.1:8000/api/v1/trials/NCT06893016
```

## Minimal frontend pages

The API app now also serves a minimal no-Node frontend:

- `GET /`
- `GET /trials/{nct_id}`

These pages are server-rendered with Jinja2 and use the existing API endpoints behind the scenes.
