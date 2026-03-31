# API Backend

This is the first backend service layer over the stored trial corpus.

## App entrypoint

- [apps/api/app/main.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/main.py)

## Current endpoint

- `GET /health`
- `POST /api/v1/search`
- `POST /api/v1/search/semantic`

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
