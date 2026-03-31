# AGENTS.md

## Project Identity

This repository is a hybrid retrieval system for:

- `2026 Cardiometabolic Trial Intelligence Assistant`

The system supports source-grounded search, trial detail inspection, and question answering over ClinicalTrials.gov trial records.

Current in-scope corpus rules:

- conditions: `obesity`, `type_2_diabetes`, `mash`
- study type: `INTERVENTIONAL`
- phases: `PHASE2`, `PHASE3`, `PHASE4`
- time focus: 2026-relevant trials

Do not silently broaden scope unless the user explicitly asks for it.

## Product Direction

The product direction is now:

- chat-first
- retrieval-grounded
- transparent

Preferred user interaction:

1. user asks a natural-language question
2. system infers filters from the question
3. system runs hybrid retrieval
4. system answers in chat
5. system shows:
   - matched trials
   - evidence snippets
   - inferred filters
   - links to trial detail

Example target interaction:

- user: `Which phase 3 obesity trials in 2026 involve GLP-1 related therapy?`
- system:
  - answers in chat
  - shows matched trials
  - shows evidence snippets
  - exposes inferred filters such as `obesity`, `PHASE3`, and `2026 relevant`

Important rule:

- chat is the primary entry point
- retrieval transparency must remain visible
- do not turn this into a generic black-box chatbot

## Current Product State

Treat the current system as an MVP checkpoint.

Already implemented:

- ClinicalTrials.gov fetch, normalize, validate, chunk, embed
- Postgres + pgvector storage
- DB-backed lexical, semantic, and fused retrieval
- grounded answer generation
- minimal FastAPI-served UI
- RQ + Redis ingestion jobs

Main user-facing workflows currently available:

- corpus search
- trial detail
- ask on a trial
- ask on the current corpus slice

Still unfinished:

- compare view
- retrieval / answer evaluation harness
- richer intervention and drug-class enrichment

## Architecture Summary

High-level flow:

1. ClinicalTrials.gov source records
2. fetch
3. normalize
4. validate
5. chunk
6. embed
7. load into Postgres + pgvector
8. retrieve with structured + lexical + semantic + fused ranking
9. generate grounded answers from retrieved evidence

Queued ingestion flow:

1. FastAPI creates ingestion job
2. RQ stores job in Redis
3. worker executes fetch/process/embed/load
4. Postgres stores job state in `ingestion_jobs`

Reference docs:

- [README.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/README.md)
- [docs/current-architecture-diagram.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/current-architecture-diagram.md)
- [docs/path-to-mvp.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/path-to-mvp.md)
- [LearningOutcomes.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/LearningOutcomes.md)

## Important Runtime Components

Backend app:

- `uvicorn apps.api.app.main:app --reload`

Worker:

- `python3 -m apps.api.app.worker`

Database migrations:

- `python3 scripts/run_db_migrations.py`

Queue stack:

- Redis
- RQ

Local environment:

- Python venv at `.venv`
- `.env` stores:
  - `OPENAI_API_KEY`
  - `DATABASE_URL`
  - `REDIS_URL`

## Backend API Surface

Current key endpoints:

- `GET /health`
- `POST /api/v1/search`
- `POST /api/v1/search/semantic`
- `POST /api/v1/search/fused`
- `POST /api/v1/ask`
- `GET /api/v1/trials/{nct_id}`
- `POST /api/v1/ingestion/jobs`
- `GET /api/v1/ingestion/jobs`
- `GET /api/v1/ingestion/jobs/{job_id}`

UI routes:

- `GET /`
- `GET /trials/{nct_id}`

## Data Model Notes

Primary tables:

- `trials`
- `trial_conditions`
- `trial_interventions`
- `trial_arms`
- `trial_outcomes`
- `trial_locations`
- `trial_eligibility`
- `trial_validation`
- `trial_chunks`
- `ingestion_jobs`

Important distinction:

- the corpus is stored in Postgres
- only `trial_chunks.embedding` uses pgvector

Do not describe the whole system as “stored in pgvector.”

## Retrieval Rules

The system is hybrid retrieval, not chatbot-first RAG.

However, the intended product UX is now chat-first over hybrid retrieval.

That means:

- chat is the front door
- hybrid retrieval is still the core engine
- filters, trial cards, and evidence remain visible supporting surfaces

Default retrieval order:

1. structured filters
2. lexical retrieval
3. semantic retrieval
4. fused ranking
5. grounded answer generation

Important behaviors:

- answers must be conservative
- answers should only use retrieved evidence
- citations should remain traceable
- chunk-type weighting is query-aware and intentional

## UI Rules

Current frontend is intentionally:

- FastAPI-served
- Jinja2-based
- minimal JavaScript
- no Node / npm build step

Do not introduce Next.js or a JS build tool unless the user explicitly asks to resume that path.

If editing the UI:

- preserve the current no-Node approach
- keep source-grounded behavior visible
- keep citation links useful and navigable
- prefer moving the product toward a chat-first workspace instead of a search-first layout
- keep matched trials, inferred filters, and evidence snippets visible alongside chat responses

## Queue / Ingestion Rules

For local macOS development:

- the worker uses `SimpleWorker`
- this avoids fork-related Objective-C crashes

If queue jobs fail:

- inspect the worker terminal first
- then inspect `GET /api/v1/ingestion/jobs/{job_id}`

When expanding the corpus:

- prefer targeted jobs by condition
- do not blindly enqueue many overlapping jobs without reason

Recommended expansion labels:

- `obesity`
- `type 2 diabetes`
- `MASH`
- `NASH`
- `NAFLD`
- `MASLD`

## Editing Rules For This Repo

- Keep changes aligned with current scope and architecture.
- Prefer extending existing services over creating parallel implementations.
- Reuse existing ingestion functions inside queued workflows instead of rewriting the ingestion path.
- Preserve deterministic ingestion behavior.
- Preserve grounded answer behavior.
- Avoid introducing broad abstractions unless the current code clearly needs them.

## Documentation Rules

When making meaningful project changes:

- update the relevant doc under `docs/`
- update [LearningOutcomes.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/LearningOutcomes.md)

For `LearningOutcomes.md` specifically:

- append new sections at the literal bottom of the file
- continue numbering from the last numbered section
- do not insert new numbered sections in the middle

## Good Next Steps

If the user asks “what next,” the most likely high-value answers are:

- expand the corpus with queued ingestion jobs
- move the UI further toward the chat-first interaction model
- build compare view
- improve taxonomy / drug-class enrichment
- add evaluation cases
- improve citation and answer UX

Do not default back into open-ended backend experimentation when a product workflow is clearly the next step.
