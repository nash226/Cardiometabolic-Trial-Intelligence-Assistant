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

See [docs/architecture.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/architecture.md), [docs/current-architecture-diagram.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/current-architecture-diagram.md), [docs/schema-and-api.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/schema-and-api.md), and [docs/path-to-mvp.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/path-to-mvp.md) for the concrete implementation target.

For the first ingestion, retrieval, storage, and backend steps, see [docs/ingestion-field-mapping.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/ingestion-field-mapping.md), [docs/raw-fetcher.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/raw-fetcher.md), [docs/normalizer.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/normalizer.md), [docs/normalization-policy.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/normalization-policy.md), [docs/validation.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/validation.md), [docs/batch-pipeline.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/batch-pipeline.md), [docs/condition-taxonomy.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/condition-taxonomy.md), [docs/chunking.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/chunking.md), [docs/lexical-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/lexical-search.md), [docs/hybrid-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/hybrid-search.md), [docs/semantic-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/semantic-search.md), [docs/fused-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/fused-search.md), [docs/database-design.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/database-design.md), [docs/database-loader.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/database-loader.md), [docs/db-retrieval.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/db-retrieval.md), [docs/db-fused-retrieval.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/db-fused-retrieval.md), [docs/api-backend.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/api-backend.md), and `scripts/run_db_migrations.py`.

For queued corpus expansion, see [docs/ingestion-jobs.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/ingestion-jobs.md).



example prompts:

- what are the top endpoints being used for child obesity studies in 2026
- I am an investor for a hedgefund, “Which upcoming obesity studies could matter next year?”
- What are some trends in interventional obesity studies in 2026
  How is this trial utilizing dual - theraphy 
- 

prompts that dont give hallucinations:
- What medications are being used for liver transplant patients?


Strategy / market:

Which phase 3 obesity trials are most likely to generate meaningful 2026 catalysts?
Which sponsors appear most active in obesity drug development for 2026?
Which obesity studies in 2026 look differentiated rather than me-too?
Which active obesity trials seem most commercially important next year?
Which studies could shift the competitive landscape in obesity in 2026?

Investor / hedge fund:

I am an investor at a hedge fund. Which obesity trials could realistically move sentiment in 2026?
Which upcoming obesity readouts in 2026 should I pay attention to first?
Which active obesity studies have the clearest near-term catalyst profile?
Which phase 2 or phase 3 obesity trials could matter for public market narratives next year?
Which obesity studies look overhyped versus actually important?
Clinical / medical:

What are the most common primary endpoints in child obesity studies in 2026?

How are pediatric obesity trials defining treatment success?
What inclusion and exclusion patterns show up most often in adolescent obesity studies?
Which obesity trials are using body weight change versus metabolic endpoints?
What endpoints are most common in interventional obesity studies that finish in 2026?

Mechanism / intervention:

How is this trial using dual therapy?
Which obesity studies appear to involve GLP-1 based combinations?
Which trials seem to be testing multi-mechanism obesity therapies?
Are there obesity studies using incretin-related combinations rather than monotherapy?
Which interventions look like combination strategies versus single-agent approaches?

Trend / synthesis:

What are the main trends in interventional obesity studies in 2026?
Are obesity studies in 2026 leaning more toward weight-loss endpoints or cardiometabolic endpoints?
What design patterns are showing up across active obesity studies in 2026?
Are sponsors favoring broad obesity populations or more targeted subgroups?
What kinds of interventions are becoming more common in the 2026 obesity pipeline?

Trial-specific:

What is the main investment takeaway from this trial?
What makes this study different from other obesity trials in the corpus?
What are the biggest risks or unknowns in this trial design?
What is this study actually trying to prove?
Why might this trial matter in the broader obesity landscape?