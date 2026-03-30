# Learning Outcomes

This file is the running review log for the project.

Each section should answer:

- what we built
- why we built it that way
- what we learned from it
- what comes next

## Current Architectural Snapshot

The system currently has three implemented ingestion layers and a documented product frame.

Current flow:

1. `fetch`
   - [scripts/fetch_trials_raw.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/fetch_trials_raw.py)
   - pulls raw ClinicalTrials.gov study records and saves them unchanged under [data/raw](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw)

2. `normalize`
   - [scripts/normalize_trial.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/normalize_trial.py)
   - converts one raw record into the project’s internal trial shape and writes it under [data/normalized](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/normalized)

3. `validate`
   - [scripts/validate_trial.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/validate_trial.py)
   - decides whether a normalized record belongs in the MVP corpus and writes the result under [data/normalized/validation](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/normalized/validation)

Current product scope:

- source: ClinicalTrials.gov
- conditions: obesity, type 2 diabetes, MASH/NAFLD
- study type: interventional only
- phase: 2 through 4
- time focus: 2026-relevant trials

Current architectural principle:

- build the system as a transparent hybrid retrieval pipeline, starting from trustworthy ingestion before UI or LLM-heavy features

## 1. Narrowing the product scope

### What we decided

We narrowed the project from a broad healthcare literature navigator into:

- `2026 Cardiometabolic Trial Intelligence Assistant`

MVP scope:

- conditions: obesity, type 2 diabetes, MASH/NAFLD
- study type: interventional only
- phase: 2 through 4
Why keep Phase 2-4?

Phase 2 starts to have meaningful efficacy, dose, and endpoint structure.
Phase 3 is highly important for competitive and clinical landscape tracking.
Phase 4 captures post-approval and real-world follow-up studies that still matter strategically.

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

## 10. Why we need parsing

### The core idea

Raw ClinicalTrials.gov records are not the same thing as our application data model.

That means the ingestion pipeline needs a step that can safely read the raw source format and extract the fields we actually care about.

### The three ingestion concepts

We should think about the ingestion pipeline in three separate layers:

#### Fetch

Job:

- download source records unchanged

What it answers:

- how do we get the source data onto disk?

Current project artifact:

- [scripts/fetch_trials_raw.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/fetch_trials_raw.py)

#### Parse

Job:

- read the raw record structure and extract usable values from nested source modules

What it answers:

- where is the field in the source record?
- how do we read it safely if the field is missing, nested, or shaped differently?

Examples:

- reading `protocolSection.statusModule.primaryCompletionDateStruct.date`
- reading `protocolSection.armsInterventionsModule.interventions[]`
- reading `protocolSection.contactsLocationsModule.locations[]`

Why parsing is necessary:

- source records are nested
- fields are optional
- arrays and objects vary by module
- some values are semi-structured or inconsistent across studies

Without a parsing layer, every downstream part of the system would need to know the raw source shape, which would make the code repetitive and fragile.

#### Normalize

Job:

- transform parsed source values into the application’s internal schema

What it answers:

- what should this field be called in our system?
- should this become a scalar field, a child record, or a derived helper field?

Examples:

- `nctId` becomes `nct_id`
- raw condition strings become `conditions` plus `condition_labels`
- source dates contribute to `is_2026_relevant`

Current project artifact:

- [scripts/normalize_trial.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/normalize_trial.py)

### Important distinction

Parser and normalizer are closely related, but they are not the same responsibility.

- parser = find and extract data from the source format
- normalizer = shape that extracted data into our internal model

In small scripts, they can live together in the same file.

But conceptually they should stay separate in our thinking, because that makes the system easier to reason about and debug.

### What I learned

- Source-oriented code and application-oriented code are not the same layer.
- Parsing protects the rest of the system from raw source complexity.
- Normalization makes retrieval and filtering stable.

## 11. Who the target user is

### Primary target user

The MVP should be built for:

- research-oriented users who need structured intelligence over cardiometabolic interventional trials

Examples:

- biotech or pharma strategy users
- clinical research analysts
- healthcare market intelligence users
- medically literate product or research users tracking the trial landscape

### Secondary target user

A secondary target user is:

- a student, analyst, founder, or builder who wants to learn the cardiometabolic trial landscape quickly

This is useful because it matches both:

- the product demo story
- the educational value of the project

### What these users actually need

They do not primarily need:

- a general medical chatbot
- personal medical advice
- diagnosis or treatment recommendations

They do need:

- fast trial search
- reliable filtering
- structured trial comparison
- source-grounded summaries
- visibility into why a trial matched the query

### Typical user questions

- Which obesity trials are recruiting right now?
- Which phase 3 studies involve GLP-1 or dual agonist therapy?
- What are the main endpoint patterns across current MASH trials?
- Which trials include adolescents?
- Which studies are industry-sponsored?

### Why this matters for system design

The target user definition influences:

- which fields we normalize
- which filters we prioritize
- which compare views we support
- how conservative the answering system should be

Because the user is research-oriented, the product should emphasize:

- structured evidence
- transparency
- citations
- non-hallucinatory summaries

### What I learned

- User definition is an architecture input, not just a product note.
- Once the user is clear, it becomes much easier to decide what data to preserve and what features matter.

## 12. Normalization policy as a contract

### What we decided

Before building validation, we agreed on explicit normalization criteria and recorded them in [docs/normalization-policy.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/normalization-policy.md).

The key principles are:

- preserve source fidelity
- use stable internal naming
- keep repeated fields as repeated structures
- derive only deterministic helper fields
- never use an LLM during normalization
- keep missingness explicit

### Why this matters

Validation should not be based on hidden coding assumptions.

It should enforce a documented contract.

That means the right order is:

1. agree on normalization policy
2. document it
3. implement validation against it

### What I learned

- A policy document can be useful even in a small project because it separates system rules from code details.
- This makes later validation decisions easier to defend and easier to change.

## 13. Validation turns normalization into corpus construction

### What we built

We created [scripts/validate_trial.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/validate_trial.py) and documented it in [docs/validation.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/validation.md).

The validator reads one normalized trial record and outputs:

- `accepted`
- `errors`
- `rejection_reasons`
- `warning_reasons`
- a compact summary block

### Why this matters

Normalization tells us what a source record becomes.

Validation tells us whether that normalized record belongs in the MVP corpus.

That distinction matters because a record can be:

- technically valid JSON
- successfully normalized
- but still out of product scope

### Current rules

Current required fields:

- `nct_id`
- `brief_title`
- `study_type`
- `overall_status`

Current rejection rules:

- not `INTERVENTIONAL`
- missing phase
- phase outside `PHASE2` to `PHASE4`
- missing normalized condition labels
- condition labels outside `obesity`, `type_2_diabetes`, or `mash`

Current warning rules:

- missing `official_title`
- missing `brief_summary`
- missing `criteria_text`
- missing locations
- missing outcomes

### What I learned

- Validation is where product scope becomes executable logic.
- This stage is what turns ingestion into corpus construction.
- Required fields, warnings, and rejection rules should be explicit rather than implicit.

### Real result

We validated a real normalized record:

- `NCT07037433`

The result was accepted with:

- study type: `INTERVENTIONAL`
- phase: `PHASE3`
- condition label: `obesity`
- 2026 relevance: `true`

### Small implementation lesson

The first validator run reported success but did not write the file where expected because the validation output path handling was wrong.

That was fixed by making the output path explicit under:

- [data/normalized/validation](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/normalized/validation)

This was a useful reminder that even simple ETL scripts need end-to-end verification, not just successful console output.

## 14. Batch processing is the first real pipeline checkpoint

### What we built

We created [scripts/process_raw_run.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/process_raw_run.py) and documented it in [docs/batch-pipeline.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/batch-pipeline.md).

The batch runner:

- reads one raw fetch run
- normalizes every study in the run
- validates every normalized study
- writes batch outputs into [data/processed_runs](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/processed_runs)
- produces a `summary.json` report

### Why this matters

Single-record processing proves that the code works in isolation.

Batch processing shows whether the pipeline works as a system.

It also gives us the first corpus-level questions:

- how many records are accepted?
- how many are rejected?
- which rejection reasons are common?
- which warnings are common?

### Real batch result

We processed:

- `data/raw/20260327T175821Z`

Summary:

- total studies: `3`
- accepted: `3`
- rejected: `0`
- warnings: `0`

Accepted NCT IDs:

- `NCT06893016`
- `NCT06974851`
- `NCT07037433`

### What I learned

- The end-to-end pipeline now works across a batch, not just individual records.
- The current sample is very homogeneous because it was fetched with tight obesity + recruiting + phase 3 filters.
- That means the batch run is useful as a mechanical checkpoint, but not yet a stress test of validation quality.

### Why that matters

A clean batch result does not necessarily mean the rules are complete.

It may just mean:

- the fetch query already pre-filtered most edge cases out

So the next time we want to test validation rigor, we should fetch a broader and messier sample.
