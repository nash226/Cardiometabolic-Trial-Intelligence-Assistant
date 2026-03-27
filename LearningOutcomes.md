# Learning Outcomes

This file is the running review log for the project.

Each section should answer:

- what we built
- why we built it that way
- what we learned from it
- what comes next

## 1. Narrowing the product scope

### What we decided

We narrowed the project from a broad healthcare literature navigator into:

- `2026 Cardiometabolic Trial Intelligence Assistant`

MVP scope:

- conditions: obesity, type 2 diabetes, MASH/NAFLD
- study type: interventional only
- phase: 2 through 4
- time focus: trials relevant to 2026
- source: ClinicalTrials.gov study records

### Why this matters

A narrow scope makes retrieval, evaluation, and answer grounding realistic.

This is stronger than a generic medical RAG app because the system now has:

- a clear dataset
- a clear user question space
- a clear filtering model
- a clear evaluation surface

### What I learned

- Product scoping is part of system design.
- A retrieval system gets easier to build once the corpus and question types are tightly defined.
- “All medical literature” is too broad for a reliable first version.

### What came next

After the scope was stable, we defined the stack, schema, and retrieval architecture.

## 2. Choosing the stack

### What we decided

We chose:

- frontend: `Next.js`
- backend: `FastAPI`
- database: `Postgres`
- vector search: `pgvector`
- lexical search: Postgres full-text search
- ingestion: Python scripts

### Why this matters

This project is not just a chatbot UI. It needs:

- structured filters
- strong backend data handling
- normalized source records
- a production-credible web app

`Next.js` was chosen over plain React because it is a more complete production framework for routing, page structure, and future streaming UX.

`FastAPI` was chosen because the ingestion and retrieval core is naturally Python-heavy.

### What I learned

- “React” is not a full stack choice by itself.
- Backend and ingestion constraints should influence frontend decisions.
- For structured RAG systems, the data layer matters more than the prompt layer early on.

### What came next

After the stack choice, we documented the architecture and schema before writing code.

## 3. Defining the ingestion architecture first

### What we decided

We chose to build the ingestion pipeline before the app scaffolding.

The ingestion pipeline is split into clear stages:

1. fetch raw records
2. normalize them
3. validate or reject them
4. derive helper fields
5. chunk for retrieval
6. store and index

### Why this matters

Everything downstream depends on ingestion:

- filters depend on normalized fields
- retrieval depends on clean text sections
- comparisons depend on structured child records
- citations depend on source fidelity

Starting with ingestion also makes the system easier to learn because each stage has one job.

### What I learned

- It is easier to understand a data system by following the data lifecycle from source to internal model.
- Building UI before data normalization would hide the most important architectural decisions.

### What came next

We wrote the field-mapping document for ClinicalTrials.gov records.

## 4. Mapping the ClinicalTrials.gov source record

### What we built

We created [docs/ingestion-field-mapping.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/ingestion-field-mapping.md).

It maps source paths from ClinicalTrials.gov study records into our normalized fields.

The most important source modules for MVP are:

- `identificationModule`
- `statusModule`
- `conditionsModule`
- `designModule`
- `armsInterventionsModule`
- `outcomesModule`
- `eligibilityModule`
- `contactsLocationsModule`
- `sponsorCollaboratorsModule`

### Why this matters

The mapping document fixes the contract between:

- raw source data
- our internal schema
- the future ETL implementation

Without this step, normalization would become guesswork.

### What I learned

- ClinicalTrials.gov records are partly structured and partly narrative.
- Some fields should copy directly.
- Some fields should become child tables or child arrays.
- Some fields should be derived during normalization, such as `is_2026_relevant`.

### What came next

We built the first executable ingestion step: the raw fetcher.

## 5. Building the raw fetcher

### What we built

We created [scripts/fetch_trials_raw.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/fetch_trials_raw.py) and documented it in [docs/raw-fetcher.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/raw-fetcher.md).

The fetcher:

- queries the ClinicalTrials.gov API v2
- downloads a small study batch
- saves raw study JSON unchanged
- writes a manifest for each run

Output structure:

- one timestamped folder per fetch run
- one raw JSON file per study
- one `manifest.json` per run

### Why this matters

This isolates the first ingestion responsibility:

- get trustworthy source data onto disk without transforming it

That makes it easy to inspect the source payload before normalization.

### What I learned

- The first version of the script used `filter.phase`, which caused a `400` error.
- The current ClinicalTrials.gov v2 API does not support a direct `filter.phase` parameter.
- Phase filtering has to go through `filter.advanced`, for example:
  - `AREA[Phase]PHASE3`

This was a useful lesson:

- real APIs often differ from intuitive parameter names
- we should verify request shapes against the actual API behavior, not assumptions

### What came next

After fetching a small real batch, we inspected raw records and then built the normalizer.

## 6. Building the first normalizer

### What we built

We created [scripts/normalize_trial.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/normalize_trial.py) and documented it in [docs/normalizer.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/normalizer.md).

The normalizer currently:

- reads one raw study JSON file
- maps it into a simpler internal shape
- writes one normalized JSON file

The normalized output contains:

- `trial`
- `conditions`
- `interventions`
- `arms`
- `outcomes`
- `locations`
- `eligibility`

### Why this matters

This is the first point where the application stops using the source format directly and starts using its own data model.

That internal model is what later powers:

- search filters
- compare views
- retrieval chunking
- grounded answer generation

### What I learned

- Some source modules map cleanly into scalar top-level fields.
- Others naturally become repeated child objects.
- Derived fields belong in normalization when they stabilize downstream behavior.

Examples of derived fields already added:

- `source_url`
- `is_2026_relevant`
- `relevance_reasons`
- `condition_labels`
- `drug_class_labels`
- `has_us_sites`

### Real data observation

One fetched study produced:

- 3 conditions
- 2 interventions
- 50 outcomes
- 726 locations

That is important because it shows:

- real trial records can be much larger than expected in some sections
- locations and outcomes may need special handling later for storage, retrieval payload size, and UI rendering

### What came next

The next ingestion step should be validation and rejection rules.

## 7. Current engineering pattern

### The pattern we are following

For each subsystem, we are trying to move in this order:

1. define the goal
2. document the shape
3. inspect real data
4. implement the smallest useful script
5. verify it on real examples
6. record what we learned

### Why this matters

This keeps the system understandable.

It also makes it easier to separate:

- source truth
- normalization logic
- derived business logic
- retrieval logic

## 8. What to review before the next step

Before moving on, review:

- [docs/ingestion-field-mapping.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/ingestion-field-mapping.md)
- [docs/raw-fetcher.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/raw-fetcher.md)
- [docs/normalizer.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/normalizer.md)
- one raw study file in [data/raw](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw)
- one normalized study file in [data/normalized](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/normalized)

## 9. Next expected learning goal

The next likely step is:

- define validation rules for accepted vs rejected studies

Questions this should answer:

- which studies are in scope?
- which studies are out of scope?
- which missing fields should cause warnings?
- which missing fields should cause rejection?

Going forward, new work should keep updating this file so the implementation and the learning trail stay in sync.
