# Path To MVP

This document defines the shortest credible path from the current backend-heavy prototype to a usable MVP.

## Current state

Already working:

- ClinicalTrials.gov fetch, normalize, validate, chunk, embed
- Postgres + pgvector storage
- DB-backed lexical retrieval
- DB-backed semantic retrieval
- DB-backed fused retrieval
- grounded answer generation API

Not yet finished for MVP:

- frontend application
- trial finder UI
- trial detail and compare views
- retrieval / answer evaluation harness
- evidence pruning and result quality cleanup

## MVP definition

The MVP is complete when a user can:

1. search the cardiometabolic trial corpus with filters
2. inspect returned trial cards with key metadata
3. open a trial detail view with grounded sections
4. ask a question and receive a source-grounded answer
5. compare a small set of trials side by side

## Recommended build order

### 1. Lock the backend contract

Goal:

- stabilize the request and response shapes the frontend will call

Required endpoints:

- `GET /health`
- `POST /api/v1/search`
- `POST /api/v1/search/semantic`
- `POST /api/v1/search/fused`
- `POST /api/v1/ask`
- `GET /api/v1/trials/{nct_id}`
- `POST /api/v1/compare`

Exit criteria:

- endpoints are stable enough that the frontend does not need to know internal DB structure

### 2. Build the trial finder UI

Goal:

- make the corpus searchable through a real interface

Current implementation choice:

- FastAPI-served HTML templates with minimal client-side JavaScript
- no Node or npm dependency for the MVP path right now

Minimum screens:

- search page
- filters sidebar
- result cards

Result cards should show:

- NCT ID
- title
- condition
- intervention
- phase
- status
- key dates

Exit criteria:

- a user can submit a query and browse real results without using curl

### 3. Build trial detail and answer panel

Goal:

- make individual trial records interpretable and support grounded Q&A

Minimum UI features:

- trial detail page
- normalized sections
- evidence snippets
- answer panel backed by `POST /api/v1/ask`

Exit criteria:

- a user can inspect a trial and ask a grounded question from the UI

### 4. Build compare view

Goal:

- support the second major product workflow after search

Minimum compare fields:

- interventions
- phase
- status
- inclusion / exclusion
- outcomes
- dates

Exit criteria:

- a user can compare 2 to 5 trials side by side

### 5. Add evaluation before polish

Goal:

- verify that retrieval and grounded answers are actually good enough for an MVP

Minimum evaluation set:

- 10 to 20 fixed questions
- expected study IDs
- basic answer-support checks

Example evaluation themes:

- recruiting phase 3 obesity trials
- GLP-1 related studies
- primary completion in 2026
- endpoint comparisons
- eligibility comparisons

Exit criteria:

- we can explain where retrieval is working and where it is failing

### 6. Quality improvements after MVP path is visible

These are important, but should follow the main product path:

- drug class enrichment
- better evidence pruning
- chunk-type weighting refinement
- answer formatting improvements
- ingestion refresh jobs
- UI polish

## Best next move

The highest-value next implementation step is:

- finish the FastAPI-served finder and detail experience
- then add the answer panel to that UI

That creates the shortest path from working backend to usable MVP.
