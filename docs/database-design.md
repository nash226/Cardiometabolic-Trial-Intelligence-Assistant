# Database Design

This document defines how the current file-based corpus maps into Postgres + pgvector.

The goal is not to change the retrieval design. The goal is to persist the design we already proved.

## Why move to Postgres + pgvector now

We already validated the retrieval architecture using:

- raw files
- normalized files
- validation outputs
- chunk files
- lexical and semantic indexes

That means the storage layer can now follow the retrieval design instead of shaping it prematurely.

Postgres + pgvector is a good fit because it lets us keep:

- structured trial metadata
- child records
- validation state
- chunk text
- lexical indexes
- semantic vectors

in one queryable system.

## Storage principles

1. Preserve trial-level structure
2. Preserve chunk-level structure
3. Preserve validation state explicitly
4. Keep source traceability
5. Keep retrieval artifacts queryable, not hidden in one blob

## Core tables

### `trials`

One row per normalized study.

Important fields:

- `id` UUID primary key
- `nct_id` text unique not null
- `source`
- `source_url`
- `brief_title`
- `official_title`
- `brief_summary`
- `detailed_description`
- `study_type`
- `phases` text[]
- `allocation`
- `intervention_model`
- `masking`
- `primary_purpose`
- `enrollment_count`
- `enrollment_type`
- `overall_status`
- `last_known_status`
- `start_date_text`
- `primary_completion_date_text`
- `completion_date_text`
- `study_first_posted_at_text`
- `results_first_posted_at_text`
- `last_update_posted_at_text`
- `is_2026_relevant`
- `relevance_reasons` text[]
- `lead_sponsor_name`
- `lead_sponsor_class`
- `collaborator_names` text[]
- `sex`
- `minimum_age_text`
- `maximum_age_text`
- `age_groups` text[]
- `healthy_volunteers`
- `condition_labels` text[]
- `intervention_labels` text[]
- `drug_class_labels` text[]
- `keyword_labels` text[]
- `country_codes` text[]
- `has_us_sites`
- `raw_has_results`
- `raw_payload` jsonb
- `created_at`
- `updated_at`

### `trial_conditions`

One row per normalized condition string.

- `id`
- `trial_id`
- `name`
- `normalized_name`
- `is_primary`

### `trial_interventions`

One row per intervention.

- `id`
- `trial_id`
- `intervention_type`
- `name`
- `normalized_name`
- `description`
- `arm_group_labels` text[]
- `drug_class`

### `trial_arms`

- `id`
- `trial_id`
- `label`
- `type`
- `description`
- `intervention_names` text[]

### `trial_outcomes`

- `id`
- `trial_id`
- `outcome_type`
- `measure`
- `description`
- `time_frame`

### `trial_locations`

- `id`
- `trial_id`
- `facility_name`
- `city`
- `state`
- `country`
- `status`

### `trial_eligibility`

One row per trial.

- `trial_id` primary key
- `criteria_text`
- `sex`
- `minimum_age_text`
- `maximum_age_text`
- `age_groups` text[]
- `healthy_volunteers`

### `trial_validation`

One row per trial validation result.

- `trial_id` primary key
- `accepted`
- `errors` text[]
- `rejection_reasons` text[]
- `warning_reasons` text[]
- `validated_at`

Why this table matters:

- validation state is part of corpus membership
- it should be queryable directly in the database

### `trial_chunks`

One row per retrieval chunk.

- `id` UUID primary key
- `chunk_id` text unique not null
- `trial_id`
- `trial_nct_id`
- `chunk_type`
- `title`
- `content`
- `source_field_paths` text[]
- `token_count_estimate`
- `content_tsv` tsvector
- `embedding` vector(1536) nullable
- `created_at`

Why `content_tsv` matters:

- this supports Postgres full-text retrieval for lexical search

Why `embedding` matters:

- this supports pgvector similarity search for semantic retrieval

## Suggested indexes

### Trial metadata indexes

- unique index on `trials(nct_id)`
- GIN on `trials(condition_labels)`
- GIN on `trials(phases)`
- GIN on `trials(relevance_reasons)`
- btree on `trials(overall_status)`
- btree on `trials(study_type)`
- btree on `trials(is_2026_relevant)`

### Child-table indexes

- btree on each child table `trial_id`

### Validation indexes

- btree on `trial_validation(accepted)`

### Chunk indexes

- unique index on `trial_chunks(chunk_id)`
- btree on `trial_chunks(trial_id)`
- btree on `trial_chunks(chunk_type)`
- GIN on `trial_chunks(content_tsv)`
- ivfflat or hnsw index on `trial_chunks.embedding` once real embeddings are loaded

## File-to-database mapping

Current file artifacts map like this:

- `data/raw/.../studies/*.json` -> `trials.raw_payload`
- `processed_runs/.../normalized/*.json` -> `trials` plus child tables
- `processed_runs/.../validation/*.json` -> `trial_validation`
- `processed_runs_with_chunks/.../chunks/*.json` -> `trial_chunks`
- semantic index vectors -> `trial_chunks.embedding`

## Recommended load order

1. insert trial row
2. insert condition, intervention, arm, outcome, location, eligibility rows
3. insert validation row
4. insert chunk rows without embeddings if needed
5. update chunk embeddings after embedding generation

This keeps the load flow close to the existing pipeline stages.

## Important decision: store only accepted trials or all trials?

Recommendation:

- store all processed trials
- store validation state explicitly
- filter to `accepted=true` at retrieval time for the MVP corpus

Why:

- rejected trials are still useful for debugging, evaluation, and future scope expansion
- deleting them would throw away useful provenance

## Next implementation step

After the schema is accepted, the next step is:

- create the SQL migration
- write a loader that inserts one processed run into Postgres
