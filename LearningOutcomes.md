# Learning Outcomes

This file is the running review log for the project.

Each section should answer:

- what we built
- why we built it that way
- what we learned from it
- what comes next

## Current Architectural Snapshot

The system currently has an implemented ingestion pipeline, persistent Postgres corpus, and API-backed retrieval.

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

4. `chunk`
   - [scripts/generate_chunks.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/generate_chunks.py)
   - creates field-aware retrieval chunks for each validated trial

5. `store`
   - [scripts/load_processed_run_to_db.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/load_processed_run_to_db.py)
   - loads trials, validation, chunks, and embeddings into Postgres + pgvector

6. `retrieve`
   - API endpoints under [apps/api/app/main.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/main.py)
   - expose DB-backed lexical, semantic, and fused retrieval

Current product scope:

- source: ClinicalTrials.gov
- conditions: obesity, type 2 diabetes, MASH/NAFLD
- study type: interventional only
- phase: 2 through 4
- time focus: 2026-relevant trials

Current architectural principle:

- build the system as a transparent hybrid retrieval pipeline, starting from trustworthy ingestion before UI or LLM-heavy features

## API Retrieval Snapshot

### What we built

The API now exposes three retrieval modes:

- `POST /api/v1/search`
- `POST /api/v1/search/semantic`
- `POST /api/v1/search/fused`

### Why this matters

This turns the retrieval pipeline into a reusable backend service instead of a collection of local scripts.

### What I learned

- lexical retrieval is strongest for exact phrase overlap
- semantic retrieval is strongest for concept-heavy phrasing
- fused retrieval combines both without hiding where the ranking came from

### What comes next

The next layer above retrieval is answer generation over retrieved chunks with grounded citations.

## Architecture Diagram

### What we built

We added a current-state architecture diagram at [current-architecture-diagram.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/current-architecture-diagram.md).

### Why this matters

The project now has enough moving parts that a visual system map is useful:

- source ingestion
- preprocessing
- storage
- retrieval API
- next-step answer generation

### What I learned

- architecture diagrams are most useful when they reflect what is actually implemented, not the imagined future system
- the cleanest way to show this project is as a hybrid retrieval pipeline with a separate future answer layer

### What comes next

The next diagram update should happen when grounded answer generation is added, so the diagram can show retrieval feeding a real synthesis layer instead of a placeholder

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

## 15. A broader sample is what reveals real rule behavior

### What we did

We fetched a broader recruiting sample using a mixed cardiometabolic query:

- `obesity OR type 2 diabetes OR MASH OR NASH OR MASLD`

Then we processed the new run through the batch pipeline:

- [data/raw/20260330T021936Z](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw/20260330T021936Z)
- [summary.json](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/processed_runs/20260330T021936Z/summary.json)

### Why this matters

The earlier obesity-only sample was too clean.

A broader fetch is what actually tests whether:

- condition normalization is good enough
- validation rules match our intended scope
- the corpus excludes the noisy records we do not want

### Real result

Summary:

- total studies: `10`
- accepted: `2`
- rejected: `8`

Top rejection reasons:

- `phase_out_of_scope`: `5`
- `missing_normalized_condition`: `3`
- `missing_phase`: `2`
- `study_type_not_interventional`: `2`

### What this tells us

The current rules are doing something meaningful now.

They are filtering out:

- observational studies
- interventional studies with `NA` phase
- phase 1 studies
- studies whose condition text our current normalizer does not map into the MVP buckets

### What I learned

- A narrow fetch can make weak rules look stronger than they are.
- Broader samples are necessary to test scope boundaries honestly.
- The current bottlenecks are now visible:
  - phase handling
  - condition terminology normalization

### Important interpretation

This result does not automatically mean the validator is too strict.

It may mean:

- the broader query is returning many studies outside our intended corpus
- our current condition-mapping logic is still too shallow for real-world naming variation

Those are different problems and should be evaluated separately.

## 16. Rejected-study review confirmed the current scope

### What we did

We inspected additional rejected studies to answer a specific question:

- are these rejections caused by weak normalization?
- or are they correct under the current product scope?

Examples reviewed:

- [NCT06303544.json](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw/20260330T021936Z/studies/NCT06303544.json)
- [NCT06642363.json](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw/20260330T021936Z/studies/NCT06642363.json)
- [NCT06715514.json](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw/20260330T021936Z/studies/NCT06715514.json)
- [NCT06894498.json](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw/20260330T021936Z/studies/NCT06894498.json)

### What we found

Most rejections are currently happening for good reasons:

- `OBSERVATIONAL` instead of `INTERVENTIONAL`
- `PHASE1`
- `NA` phase
- truly out-of-scope conditions such as type 1 diabetes

The most ambiguous cases were interventional studies with correct condition matching but `NA` phase.

Those were still rejected correctly under the current MVP definition because we intentionally decided to keep:

- phase `2` through `4` only

### Decision

We are keeping the current scope as-is.

That means:

- do not broaden to `NA` phase interventional studies
- do not loosen phase rules right now
- do not change the validator based on these reviewed examples

### What I learned

- Reviewing rejected examples is necessary before changing rules.
- A rejected study can look interesting without actually belonging in the corpus.
- The current validator appears to be enforcing scope more than it is exposing normalization bugs.

### What comes next

Since scope stays fixed, the next useful ingestion improvement is:

- condition taxonomy

That is a better next step than changing validation, because it improves terminology handling without changing the product boundary.

## 17. Condition taxonomy is now its own ingestion layer

### What we built

We moved condition mapping logic out of the normalizer and into a dedicated taxonomy layer:

- [scripts/lib/condition_taxonomy.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/lib/condition_taxonomy.py)
- [scripts/lib/condition_taxonomy.json](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/lib/condition_taxonomy.json)
- [docs/condition-taxonomy.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/condition-taxonomy.md)

The normalizer now calls the taxonomy module instead of keeping condition rules inline.

### Why this matters

Condition terminology is its own problem.

Separating it from the main normalizer makes it easier to:

- inspect mappings directly
- update terminology safely
- keep normalization code focused on structure, not taxonomy policy

### Current taxonomy design

The taxonomy currently uses:

- explicit mappings for known labels
- simple contains-rules for broader matching

condition taxonomy = our rulebook for turning many source condition names into a few stable project categories.

Current stable labels:

- `obesity`
- `type_2_diabetes`
- `mash`

### What I learned

- Pulling taxonomy into its own layer improves clarity even if behavior does not change yet.
- This is a good example of turning hidden logic into inspectable data.

### Verification result

We reran the broader batch after the taxonomy refactor and got the same acceptance and rejection counts as before.

That is good.

It means:

- the refactor preserved current behavior
- the system is now cleaner without silently changing corpus membership

## 18. Chunking is the first ingestion layer built for retrieval

### What we built

We created [scripts/generate_chunks.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/generate_chunks.py) and documented it in [docs/chunking.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/chunking.md).

The chunk generator turns one normalized trial record into field-aware retrieval chunks.

Current chunk types:

- `status_identity`
- `conditions_interventions`
- `summary_description`
- `eligibility`
- `outcomes`
- `timeline`
- `sponsor_locations`

### Why this matters

This is the first ingestion layer that directly shapes retrieval quality.

Without chunking, we would have to retrieve:

- either one giant trial blob
- or arbitrary fixed-size windows

Both are worse than field-aware chunks for this dataset.

### What I learned

- Trial records are semi-structured enough that chunking by section is more sensible than chunking by token count alone.
- `source_field_paths` are important because they preserve traceability for later citations and debugging.
- Location data needs to be sampled carefully because some studies have very large site arrays.

### Batch integration

We also updated [scripts/process_raw_run.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/process_raw_run.py) so processed runs now include:

- normalized records
- validation outputs
- chunk files
- a summary report

That means one raw run can now produce retrieval-ready artifacts end to end.

### Chunking strategy details

The chunking strategy we are using is:

- field-aware chunking

This means we do not split trial records into arbitrary 300-token or 500-token windows.

Instead, we create chunks based on meaningful trial sections:

- identity and status
- conditions and interventions
- summary and description
- eligibility
- outcomes
- timeline
- sponsor and locations

Why this strategy fits this dataset:

- ClinicalTrials.gov records are semi-structured
- users ask section-specific questions
- citations need to map back to understandable source fields

Examples:

- a question about inclusion criteria should match the `eligibility` chunk
- a question about endpoints should match the `outcomes` chunk
- a question about recruiting status or completion dates should match the `status_identity` or `timeline` chunk

### Why we are not using fixed-size chunks

We are avoiding generic fixed-token chunking because it can mix unrelated information such as:

- eligibility text
- outcome measures
- sponsor metadata
- dates

That would weaken:

- retrieval precision
- explanation quality
- source-grounded citation

### Important tradeoff

Field-aware chunks are usually better for precision, but some sections can still get large.

Current examples:

- eligibility criteria can be long
- outcome lists can be long
- location lists can be very large

Our current handling:

- keep eligibility as one section-level chunk
- keep outcomes grouped for now
- sample location content instead of dumping every site into the chunk

This is a practical MVP tradeoff.

If retrieval quality later suffers, we can split large sections more finely without changing the overall section-based strategy.

### What exactly is being chunked

We are chunking:

- the normalized trial record

We are not chunking:

- the raw ClinicalTrials.gov JSON directly
- arbitrary token windows
- PDFs

The chunk generator reads normalized sections such as:

- `trial`
- `conditions`
- `interventions`
- `arms`
- `outcomes`
- `locations`
- `eligibility`

Then it groups those into section-level retrieval units.

### Sample chunk examples

From [NCT06893016.json](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/chunks/NCT06893016.json):

`status_identity`

```text
NCT ID: NCT06893016
Brief title: Evaluation of RAY1225 in Adult Participants Who Have Obesity or Are Overweight
Official title: A Multicenter, Randomized, Double-blind, Placebo-controlled Phase 3 Study Evaluating the Safety, Tolerability, and Efficacy of RAY1225 in Participants Who Have Obesity or Are Overweight
Study type: INTERVENTIONAL
Overall status: RECRUITING
Phases: PHASE3
```

`conditions_interventions`

```text
Condition labels: obesity
Raw conditions: Obesity
Intervention labels: RAY1225; Placebo
Drug class labels:
Arms: RAY1225 High Dose; RAY1225 Medium Dose; RAY1225 Low Dose; Placebo
Keywords:
```

`timeline`

```text
Start date: 2025-06-15
Primary completion date: 2026-06-15
Completion date: 2026-09-15
Study first posted: 2025-03-25
Results first posted: None
Last update posted: 2025-07-17
2026 relevant: True
Relevance reasons: active_or_recruiting_status; primary_completion_in_2026; completion_in_2026
```

### Metadata that ties chunks back to the trial

Each chunk is not just plain text. It also carries metadata that links it back to the source trial.

Important fields:

- `trial_nct_id`
- `chunk_id`
- `source_field_paths`

Example:

- `trial_nct_id: NCT06893016`
- `chunk_id: NCT06893016:timeline:6`

Why this matters:

- retrieved chunks can always be grouped back under the original trial
- the system can cite the original study ID in answers
- we can explain which fields were used to build the chunk
- later retrieval can surface both chunk-level evidence and trial-level identity

## 19. Lexical search is the first retrieval layer

### What we built

We created:

- [scripts/build_chunk_index.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/build_chunk_index.py)
- [scripts/search_chunks.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/search_chunks.py)
- [docs/lexical-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/lexical-search.md)

This is a simple lexical retrieval system over chunk files.

### How it works

The current retrieval flow is:

1. read chunk files
2. tokenize chunk content
3. build an inverted index from token to chunk IDs
4. store chunk metadata alongside postings
5. run keyword search over the index

Current search output includes:

- `score`
- `chunk_id`
- `trial_nct_id`
- `chunk_type`
- `title`
- `snippet`
- `source_field_paths`

### Why we started with lexical search

Lexical search is the right first retrieval layer because it is:

- transparent
- easy to debug
- useful for exact terms such as drug names, phases, endpoint terms, and sponsors

This gives us a real retrieval system before introducing embeddings.

### Real query examples

Query:

- `type 2 diabetes`

Returned chunks from:

- `NCT06715514`
- `NCT06748963`
- `NCT06474598`

Query:

- `primary completion`

Returned `timeline` chunks, which is exactly what we want because that phrase belongs to trial date metadata.

Query:

- `GLP-1`

Returned chunks from:

- `NCT06715514` outcomes
- `NCT06715514` conditions/interventions
- `NCT06715514` status/identity
- and one eligibility match from `NCT06893016`

### What I learned

- The chunk design is already helping retrieval because section-specific phrases tend to land in the right chunk types.
- Exact-term retrieval is a strong first baseline in this domain.
- Build and search should happen sequentially, not in parallel, because the search script depends on the completed index file.

### Current limitation

The search is still intentionally simple:

- no stemming
- no synonym expansion
- no structured filter integration
- no semantic retrieval yet

That is acceptable because the current goal is a clean lexical baseline.

## 20. Hybrid retrieval means filters first, text search second

### What we built

We created [scripts/hybrid_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/hybrid_search.py) and documented it in [docs/hybrid-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/hybrid-search.md).

This is the first retrieval layer that combines:

- structured trial filters
- lexical chunk search

### How it works

The current flow is:

1. read a processed-run summary
2. select eligible trials using metadata filters
3. run lexical scoring only over chunks from those trials
4. return chunk-level hits with trial IDs and snippets

Current filters:

- `condition`
- `phase`
- `study_type`
- `accepted_only`
- `year_2026_only`

### Why this matters

This is closer to the actual product than lexical search alone.

It means the system can answer questions like:

- find chunks about `primary completion` from accepted phase 3 obesity trials

instead of just:

- find any chunk anywhere that contains the words `primary` and `completion`

### Real example

Query:

- `primary completion`

Filters:

- `condition=obesity`
- `phase=PHASE3`
- `study_type=INTERVENTIONAL`
- `accepted_only=true`
- `year_2026_only=true`

Result:

- exactly one eligible trial
- `NCT06893016`
- top hit was its `timeline` chunk

That is the expected behavior.

### Another useful example

Query:

- `GLP-1`

Filters:

- `condition=type_2_diabetes`
- `study_type=INTERVENTIONAL`
- `accepted_only=true`
- `year_2026_only=true`

Result:

- no hits

Why that is useful:

- it shows the structured filters are actually restricting search
- the system is not pretending to have matching in-scope evidence when the current accepted sample does not contain it

### What I learned

- Hybrid retrieval is not just better ranking; it is better eligibility control.
- Empty results can be a correct outcome when the filtered corpus truly has no matching chunk.
- This makes the retrieval system more honest and more aligned with the product scope.

## 21. Semantic retrieval is now wired in, with a development-safe fallback

### What we built

We created:

- [scripts/build_chunk_embeddings.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/build_chunk_embeddings.py)
- [scripts/semantic_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/semantic_search.py)
- [scripts/lib/embedding_utils.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/lib/embedding_utils.py)
- [docs/semantic-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/semantic-search.md)

### Provider strategy

The semantic layer supports two providers:

- `local_debug`
- `openai`

`local_debug` is a deterministic hashed embedding used for:

- offline development
- architecture testing
- plumbing verification

`openai` is the path to real semantic embeddings when:

- network access is available
- `OPENAI_API_KEY` is set
- a real embedding model is configured

### Why this matters

This lets us build the semantic retrieval architecture now without blocking on external API availability.

That is useful because we can verify:

- index format
- embedding storage
- cosine-similarity search
- result output shape

before we depend on real hosted embeddings.

### Real results

Query:

- `trial completion date`

Returned mostly `timeline` chunks, which is a good sign because that concept belongs in timeline metadata.

Query:

- `incretin obesity therapy`

Returned obesity and GLP-1-related chunks, but the quality is still limited by the `local_debug` embedding method.

### Important limitation

The current semantic layer is:

- architecture-complete
- quality-incomplete

That means:

- the pipeline is ready for real embeddings
- but current semantic quality should not be treated as production-ready

### What I learned

- It is useful to separate retrieval architecture from model quality.
- A local fallback makes it possible to keep building the system even when external API access is unavailable.
- The next time we enable real embeddings, we should compare:
  - lexical results
  - hybrid lexical results
  - semantic results
  - combined retrieval behavior

## 22. Comparing semantic retrieval to lexical and hybrid retrieval

### What we did

We ran the same types of queries across:

- lexical search
- structured + lexical hybrid search
- semantic search using the OpenAI embeddings index

### Query 1: `incretin obesity therapy`

#### Semantic search

Semantic search returned conceptually related chunks including:

- `NCT06715514` GLP-1-related identity and intervention chunks
- `NCT07314684` GLP1-RA-related identity and summary chunks
- obesity-related chunks from `NCT06893016`

This is useful because the query did not rely only on exact term overlap.

#### Lexical search

Lexical search found some related material too, but it mixed:

- relevant GLP-1-related chunks
- obesity chunks that matched mostly on literal keyword overlap

#### Hybrid lexical search

With filters constrained to accepted obesity interventional 2026-relevant trials, hybrid search returned only `NCT06893016` chunks.

That is also useful because it shows:

- structured filters can intentionally narrow the retrieval space
- but they can also exclude semantically related cross-condition material when the filter is tight

### Query 2: `trial completion date`

#### Semantic search

Semantic search returned mostly `timeline` chunks.

That is a strong sign that:

- the chunk design is sensible
- the semantic index is finding the right section type for this query

#### Lexical search

Lexical search also returned many `timeline` chunks, but it surfaced at least one less-useful summary chunk because of exact word overlap with `trial`.

#### Hybrid lexical search

Hybrid retrieval restricted results to the accepted in-scope interventional 2026-relevant trials, which produced a cleaner result set:

- `NCT06893016`
- `NCT07314684`

### What I learned

- Semantic retrieval helps most on concept-heavy queries where wording may vary.
- Lexical retrieval remains strong for explicit metadata-style phrases.
- Hybrid lexical retrieval is best when the user intent includes clear structured constraints.
- Semantic retrieval without structured filtering can surface relevant but out-of-scope trials.

### Practical takeaway

The three retrieval modes are best at different things:

- lexical: exact terms
- hybrid lexical: exact terms inside the right trial subset
- semantic: concept similarity across varied wording

That means the next real retrieval improvement should be:

- a combined ranking or fusion layer

instead of replacing one method with another.

## 23. Fused retrieval combines lexical and semantic signals explicitly

### What we built

We created:

- [scripts/fused_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/fused_search.py)
- [docs/fused-search.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/fused-search.md)

The fused layer:

- applies structured trial filters
- computes lexical scores
- computes semantic scores
- normalizes both score families
- combines them with configurable weights

### Why this matters

This is the first layer that treats lexical and semantic retrieval as complementary signals instead of separate tools.

It also keeps the system transparent because every result reports:

- lexical raw score
- semantic raw score
- lexical normalized score
- semantic normalized score
- fused score

### Real result: concept-heavy query

Query:

- `incretin obesity therapy`

With:

- `accepted_only`
- `study_type=INTERVENTIONAL`
- `year_2026_only=true`
- weights `lexical=0.4`, `semantic=0.6`

The top fused results included:

- `NCT07314684` outcomes
- `NCT07314684` summary
- `NCT06893016` conditions/interventions

This shows semantic similarity contributing strongly where exact lexical overlap is weaker.

### Real result: metadata-style query

Query:

- `trial completion date`

With:

- `accepted_only`
- `study_type=INTERVENTIONAL`
- `year_2026_only=true`
- weights `lexical=0.6`, `semantic=0.4`

The top fused results were:

- `NCT06893016` timeline
- `NCT07314684` timeline

This is what we want because date-oriented queries benefit heavily from lexical precision and the timeline chunk structure.

### What I learned

- Fused retrieval lets us tune behavior by query style.
- Concept-heavy queries benefit more from semantic weight.
- metadata-style queries benefit more from lexical weight.
- score transparency makes it much easier to reason about why a result ranked where it did.

## 24. The storage layer is now designed for Postgres + pgvector

### What we built

We created:

- [docs/database-design.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/database-design.md)
- [001_init_trial_corpus.sql](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/db/migrations/001_init_trial_corpus.sql)

This is the first concrete database target for the corpus.

### Why this matters

Until now, the retrieval pipeline has been proven with file-based artifacts.

That was the right choice for learning and debugging.

Now that the corpus shape and retrieval design are stable enough, the storage layer can become persistent without changing the architecture.

### Core storage decision

We are storing:

- trial metadata
- child records
- validation state
- chunk text
- lexical search vectors
- semantic vectors

inside Postgres + pgvector.

### Important design choice

We decided to store:

- all processed trials

not just accepted trials.

Why:

- rejected trials are still useful for debugging, evaluation, and future scope changes
- retrieval can filter on validation state instead of deleting provenance

### What I learned

- Storage should follow the retrieval design, not precede it.
- By delaying the database until after retrieval logic was proven, we ended up with a cleaner schema and clearer mapping from files to tables.

## 25. The database loader now bridges file artifacts into Postgres

### What we built

We created:

- [scripts/load_processed_run_to_db.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/load_processed_run_to_db.py)
- [docs/database-loader.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/database-loader.md)

This is the step that takes a processed run and loads it into the Postgres + pgvector schema.

### What it loads

For each study in a processed run, the loader reads:

- raw payload
- normalized payload
- validation payload
- chunk payload
- optional semantic embeddings

Then it writes:

- `trials`
- child tables
- `trial_validation`
- `trial_chunks`

### Why this matters

This is the first executable step that turns the storage design into an actual persistence path.

It means the project now has:

- a proven file-based pipeline
- a concrete database schema
- and a loader to bridge between them

### Important implementation choice

The loader currently refreshes child rows per trial instead of trying to do a more complex partial sync.

That is acceptable for now because the priority is:

- correctness
- clarity
- deterministic behavior

not maximum ingestion throughput.

## 26. DB semantic retrieval follows the same backend pattern

### What we built

We created:

- [scripts/db_semantic_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/db_semantic_search.py)

This script:

- embeds the query
- applies structured trial filters
- runs pgvector similarity against `trial_chunks.embedding`

### Why this matters

This is the semantic counterpart to the DB lexical retrieval script.

It means the backend retrieval layer can now support both:

- `content_tsv` lexical search
- `embedding` vector search

from the stored corpus.

### What I learned

- Once retrieval is DB-backed, lexical and semantic search can share the same storage layer while still using different query operators.
- Environment consistency matters more here because the Python runtime now needs:
  - database access
  - embedding provider access

## 27. The retrieval scripts now have an API boundary

### What we built

We created a minimal FastAPI backend under:

- [apps/api/app/main.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/main.py)

Supporting pieces:

- config loading
- DB connection helper
- typed search request and response schemas
- a search service over the stored corpus

### Current endpoint

- `POST /api/v1/search`

### Why this matters

This is the transition from:

- retrieval as local scripts

to:

- retrieval as an application backend service

That matters because the frontend should call a stable API contract, not raw scripts.

### What I learned

- Once retrieval logic is stable, wrapping it in an API gives the project a real backend boundary.
- API work also introduces another environment contract:
  - FastAPI and Pydantic now need to be installed in the venv

## 28. The API now exposes both lexical and semantic retrieval

### What we built

We added a semantic retrieval endpoint:

- `POST /api/v1/search/semantic`

Backed by:

- [apps/api/app/services/semantic_search_service.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/app/services/semantic_search_service.py)

### Why this matters

This gives the product a real semantic retrieval interface, not just a local script.

That means the frontend or any client can now compare:

- lexical endpoint behavior
- semantic endpoint behavior

through the same backend application.

### What I learned

- It is often cleaner to expose semantic retrieval as a separate endpoint first instead of overloading the lexical endpoint immediately.
- That keeps comparison easy while the retrieval behavior is still being tuned.


## 29. Grounded Answer Generation

### What we built

We added a first answer-generation endpoint:

- `POST /api/v1/ask`

It retrieves evidence with fused search, then synthesizes an answer from those retrieved chunks.

### Why this matters

This is the first point where the system behaves like a user-facing intelligence assistant instead of only a retrieval backend.

The key design choice is still grounded behavior:

- retrieve first
- answer second
- return citations with the answer
- fall back to extractive evidence if synthesis is unavailable

### What I learned

- answer generation should be downstream of a stable retrieval interface, not mixed directly into database queries
- a useful first answer layer is conservative and citation-heavy, not conversationally broad
- fallback behavior matters because retrieval can succeed even when generation fails

### What comes next

The next likely step is either:

- add richer answer formatting and trial-level grouping, or
- build evaluation cases that score whether answers are supported by the retrieved evidence

## 30. Query-Aware Chunk Weighting

### What we built

We updated fused retrieval to apply query-aware chunk-type weighting before the final ranking.

This affects:

- `POST /api/v1/search/fused`
- `POST /api/v1/ask`

### Why this matters

Not all chunk types are equally useful for every question.

Examples:

- therapy questions should favor `conditions_interventions`
- eligibility questions should favor `eligibility`
- completion and status questions should favor `timeline`
- endpoint questions should favor `outcomes`

Without this step, a semantically similar but weak chunk like `eligibility` can outrank a more useful intervention chunk for treatment questions.

### What I learned

- retrieval quality is not only about lexical vs semantic scoring
- chunk selection quality also depends on ranking the right section types for the question intent
- this is a ranking improvement, not a scope change or an LLM prompt change

### What comes next

The next improvement after chunk-type weighting is likely one of:

- intervention / drug-class enrichment so queries like `incretin` can map more directly to trial interventions
- retrieval evaluation to measure whether the new weighting improves evidence quality consistently

## 31. OpenAI SDK Refactor

### What we built

We refactored the OpenAI integration to use the official Python SDK instead of raw HTTP calls.

This changed two paths:

- embeddings now use `client.embeddings.create(...)`
- answer generation now uses `client.responses.create(...)`

### Why this matters

The SDK is a better long-term integration surface than hand-written `urllib` requests.

It gives us:

- cleaner client code
- better alignment with the current OpenAI API surface
- easier future upgrades for response generation

### What I learned

- embeddings and answer generation are two separate model interaction paths in this system
- `responses.create(...)` is the right abstraction for answer generation
- embeddings should still use the embeddings API through the SDK

### What comes next

The next step is to reinstall dependencies in the venv and rerun:

- semantic retrieval
- fused retrieval
- grounded answer generation

to verify the SDK-backed path end to end

## 32. Path To MVP

### What we built

We added a dedicated MVP path document at [path-to-mvp.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/path-to-mvp.md).

### Why this matters

The project now has enough backend capability that the main question is no longer “can this architecture work?”

The main question is:

- what is the shortest path to a usable product?

The MVP path document answers that by separating:

- must-have product steps
- quality improvements that can come after

### What I learned

- once the backend core is working, the biggest risk becomes losing focus and continuing to optimize internals instead of finishing the user-facing product
- the cleanest MVP sequence is backend contract first, then finder UI, then detail/ask, then compare, then evaluation

### What comes next

The next build step should be:

- `GET /api/v1/trials/{nct_id}`

After that, the frontend trial finder can start against a stable backend contract.

## 33. Trial Detail Endpoint

### What we built

We added:

- `GET /api/v1/trials/{nct_id}`

This endpoint returns one stored trial with:

- core trial metadata
- conditions
- interventions
- arms
- outcomes
- locations
- eligibility
- validation state
- chunk previews

### Why this matters

This is the missing backend contract for the product path.

It gives the frontend a stable way to move from:

- search results

to:

- a real trial detail page

without exposing raw database tables directly.

### What I learned

- a usable MVP needs detail endpoints, not just search endpoints
- storing normalized child records pays off here because the API can return a clean trial object instead of forcing the frontend to reconstruct it

### What comes next

The next product step should be:

- start the Next.js trial finder UI against the search and trial-detail endpoints

## 34. Minimal No-Node Finder UI

### What we built

We added a minimal FastAPI-served frontend:

- `GET /`
- `GET /trials/{nct_id}`

This uses Jinja2 templates and lightweight browser-side JavaScript instead of a Node-based frontend stack.

### Why this matters

This keeps the MVP path moving without introducing npm-based frontend tooling right now.

It gives us:

- a search page over the stored corpus
- result drill-down into trial detail
- a safer frontend path while supply-chain concerns remain

### What I learned

- once the backend contracts are stable, a minimal template-based UI is enough to turn the system into a usable MVP shell
- we do not need a full frontend framework to validate the core product workflows

### What comes next

The next UI step should be:

- add the grounded answer panel to the trial detail or search experience
