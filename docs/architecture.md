# Architecture

See the current system diagram at [current-architecture-diagram.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/current-architecture-diagram.md).

## System shape

The MVP is a hybrid retrieval application over ClinicalTrials.gov study records. It is not a free-form literature chatbot.

The system has four major layers:

1. Ingestion and normalization
2. Indexed retrieval
3. Answer synthesis
4. Web application

## Ingestion pipeline

Primary source:

- ClinicalTrials.gov API records for interventional cardiometabolic studies

Pipeline:

1. Fetch source records by query and study metadata
2. Validate the raw payload shape
3. Normalize records into a stable internal schema
4. Generate field-aware retrieval chunks
5. Store records, chunks, and embeddings

## Data selection rules

Include only studies that satisfy all of the following:

- Interventional studies
- Condition overlap with obesity, type 2 diabetes, or MASH/NAFLD
- Phase 2, phase 3, or phase 4
- Relevant to 2026 by recruiting status, active status, primary completion date, completion date, or result/reporting activity

Geography stays broad for MVP. Filtering by country should be a query-time capability, not a hard ingestion exclusion.

## Chunking strategy

Chunk records by semantic field groups rather than by fixed token windows.

Recommended chunk types:

- `status_identity`: NCT ID, brief title, official title, phase, status, study type
- `conditions_interventions`: conditions, interventions, arm groups, keywords
- `summary_description`: brief summary and detailed description
- `eligibility`: inclusion and exclusion criteria, sex, age ranges, healthy volunteers
- `outcomes`: primary and secondary outcomes with time frames
- `timeline`: start date, primary completion date, completion date, posted and updated dates
- `sponsor_locations`: sponsor, collaborators, location countries, site summaries

Benefits:

- better retrieval precision
- easier field citation
- easier match explanation
- less contamination between unrelated fields

## Retrieval pipeline

### 1. Structured filtering

Use normalized fields first to narrow the candidate pool.

Supported filters:

- condition
- intervention or drug class
- phase
- recruitment status
- sponsor type
- age group
- geography
- 2026 relevance window

### 2. Lexical retrieval

Run full-text search over normalized fields and narrative chunks for exact or near-exact terms such as:

- `GLP-1`
- `tirzepatide`
- `adolescent`
- `primary completion`
- `cardiovascular outcomes`

### 3. Semantic retrieval

Run vector similarity over field-aware chunks to capture broader concepts such as:

- incretin-based obesity therapy
- MASH trials enrolling patients with diabetes
- cardiometabolic outcome studies with metabolic overlap

### 4. Rank fusion

Combine signals from:

- filter match quality
- lexical score
- semantic score
- chunk type weighting

This can begin as a hand-tuned weighted score. A dedicated reranker is optional later.

### 5. Grounded synthesis

The LLM receives only the final retrieved record set and cited chunks. It should:

- answer only from retrieved evidence
- cite the source fields used
- separate direct facts from inference
- state when a field is absent or unclear

## Explainability

Each result should expose a `why_matched` view:

- matched filters
- matched keywords
- matched semantic chunk types
- fields used in the final answer

This is a core product feature, not a debug tool.

## Frontend surfaces

The MVP UI should include:

1. Search page with filters and result cards
2. Trial detail page with normalized sections and evidence snippets
3. Compare page for 2 to 5 trials
4. Ask page or answer panel over current search results

## Non-goals for MVP

- full PubMed or journal ingestion
- guideline retrieval
- clinician decision support
- unsupported medical recommendations
- broad all-domain trial coverage
