# 2026 Cardiometabolic Trial Intelligence Assistant

Source-grounded search, comparison, and question answering over interventional cardiometabolic trials relevant to 2026.

## MVP scope

- Conditions: obesity, type 2 diabetes, MASH/NAFLD
- Study type: interventional only
- Phase: 2 through 4
- Time focus: trials recruiting in 2026, active in 2026, completing in 2026, or reporting results in 2026
- Geography: US + global
- Primary data source: ClinicalTrials.gov study records

## Product goals

The application should support four workflows:

1. Trial finder with structured filters
2. Trial detail summaries with source-grounded fields
3. Trial comparison across 2 to 5 studies
4. Question answering over retrieved trials with explicit citations

## Stack decision

- Frontend: Next.js
- Backend API: FastAPI
- Database: Postgres
- Vector search: pgvector
- Lexical retrieval: Postgres full-text search
- Ingestion and normalization: Python ETL
- LLM synthesis: OpenAI API
- Evaluation: pytest with a fixed question set and expected study IDs

## Why this stack

- Next.js gives a production-grade React app structure for multi-page search and compare workflows.
- FastAPI is a strong fit for ETL-heavy Python services and retrieval APIs.
- Postgres + pgvector keeps structured filters, metadata, and vector search in one place.
- ClinicalTrials.gov records are partly structured and partly narrative, so hybrid retrieval is a better fit than pure semantic RAG.

## Retrieval approach

1. Structured filtering on normalized trial fields
2. Lexical retrieval over key narrative sections
3. Semantic retrieval over field-aware chunks
4. Optional reranking for final candidate ordering
5. LLM synthesis constrained to retrieved records and cited fields

The assistant must answer conservatively, distinguish facts from inference, and explicitly state when a field is missing or ambiguous.

## Initial deliverables

- Normalized trial schema
- ClinicalTrials.gov ingestion pipeline
- Hybrid retrieval service
- Search and compare UI
- Source-grounded answer panel
- Basic offline evaluation suite

See [docs/architecture.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/architecture.md) and [docs/schema-and-api.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/schema-and-api.md) for the concrete implementation target.

For the first ingestion steps, see [docs/ingestion-field-mapping.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/ingestion-field-mapping.md), [docs/raw-fetcher.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/raw-fetcher.md), [docs/normalizer.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/normalizer.md), [docs/normalization-policy.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/normalization-policy.md), [docs/validation.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/validation.md), and [docs/batch-pipeline.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/batch-pipeline.md).
