# Ingestion Jobs

This adds an `RQ + Redis` job queue for corpus expansion.

## What it does

The queued ingestion path runs the full corpus expansion flow:

1. fetch raw studies from ClinicalTrials.gov
2. process the raw run into normalized, validation, and chunk outputs
3. build semantic embeddings for the processed chunks
4. load the processed run into Postgres

## Backend pieces

- API endpoints in [main.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/main.py)
- job service in [ingestion_job_service.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/services/ingestion_job_service.py)
- worker entrypoint in [worker.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/worker.py)
- job table migration in [002_ingestion_jobs.sql](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/db/migrations/002_ingestion_jobs.sql)

## API endpoints

- `POST /api/v1/ingestion/jobs`
- `GET /api/v1/ingestion/jobs`
- `GET /api/v1/ingestion/jobs/{job_id}`

## Required environment

- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`

`REDIS_URL` defaults to `redis://localhost:6379/0` if omitted.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Apply migration

```bash
python3 scripts/run_db_migrations.py
```

## Run Redis

Example if Redis is installed locally:

```bash
redis-server
```

## Run the worker

In a separate terminal with the venv activated:

```bash
python3 -m apps.api.app.worker
```

For local macOS development, this worker uses `SimpleWorker` instead of the default fork-based worker. That avoids the Objective-C fork safety crash that can happen with Python jobs calling networked libraries.

## Create a job

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ingestion/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "query_cond": "obesity",
    "filter_overall_status": ["RECRUITING", "ACTIVE_NOT_RECRUITING"],
    "filter_phase": ["PHASE2", "PHASE3", "PHASE4"],
    "max_studies": 100,
    "page_size": 50,
    "embedding_provider": "openai",
    "embedding_model": "text-embedding-3-small"
  }'
```

## Inspect jobs

```bash
curl http://127.0.0.1:8000/api/v1/ingestion/jobs
```

```bash
curl http://127.0.0.1:8000/api/v1/ingestion/jobs/<job_id>
```
