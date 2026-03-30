# Schema And API

## Normalized trial schema

The internal model should preserve raw source fidelity while exposing reliable fields for filtering and retrieval.

### `trials`

One row per study.

Core identifiers:

- `id`: internal UUID
- `nct_id`: string, unique
- `source`: string, default `clinicaltrials_gov`
- `source_url`: string

Identity:

- `brief_title`: string
- `official_title`: string nullable
- `brief_summary`: text nullable
- `detailed_description`: text nullable

Study design:

- `study_type`: string
- `phases`: string array
- `allocation`: string nullable
- `intervention_model`: string nullable
- `masking`: string nullable
- `primary_purpose`: string nullable

Status and timeline:

- `overall_status`: string
- `start_date`: date nullable
- `primary_completion_date`: date nullable
- `completion_date`: date nullable
- `study_first_posted_at`: date nullable
- `results_first_posted_at`: date nullable
- `last_update_posted_at`: date nullable
- `is_2026_relevant`: boolean
- `relevance_reasons`: string array

Enrollment:

- `enrollment_count`: integer nullable
- `enrollment_type`: string nullable

Sponsor:

- `lead_sponsor_name`: string nullable
- `lead_sponsor_class`: string nullable
- `collaborator_names`: string array

Population:

- `sex`: string nullable
- `minimum_age_text`: string nullable
- `maximum_age_text`: string nullable
- `healthy_volunteers`: string nullable
- `age_groups`: string array

Denormalized search helpers:

- `condition_labels`: string array
- `intervention_labels`: string array
- `drug_class_labels`: string array
- `keyword_labels`: string array
- `country_codes`: string array
- `has_us_sites`: boolean

Audit:

- `raw_payload`: jsonb
- `created_at`: timestamptz
- `updated_at`: timestamptz

### `trial_conditions`

- `trial_id`
- `name`
- `normalized_name`
- `is_primary`

### `trial_interventions`

- `trial_id`
- `intervention_type`
- `name`
- `normalized_name`
- `drug_class`

### `trial_arms`

- `trial_id`
- `label`
- `type`
- `description`

### `trial_outcomes`

- `trial_id`
- `outcome_type`
- `measure`
- `description`
- `time_frame`

### `trial_locations`

- `trial_id`
- `facility_name`
- `city`
- `state`
- `country`
- `status`

### `trial_eligibility`

- `trial_id`
- `criteria_text`
- `inclusion_text`
- `exclusion_text`

### `trial_chunks`

Field-aware retrieval units.

- `id`
- `trial_id`
- `chunk_type`
- `title`
- `content`
- `source_field_paths`: string array
- `token_count`
- `embedding`: vector
- `tsv`: tsvector

See [database-design.md](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/docs/database-design.md) and [001_init_trial_corpus.sql](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/apps/api/db/migrations/001_init_trial_corpus.sql) for the concrete Postgres + pgvector storage design.

## 2026 relevance logic

Mark a trial as relevant if one or more of the following is true:

- `overall_status` indicates recruiting, active, or not yet completed during 2026
- `primary_completion_date` is in 2026
- `completion_date` is in 2026
- `results_first_posted_at` is in 2026
- another explicit 2026 trial milestone is present in source metadata

Store the reason in `relevance_reasons` so this can be filtered and explained.

## API surface

### `GET /api/v1/trials`

Structured search endpoint.

Query params:

- `condition`
- `intervention`
- `drug_class`
- `phase`
- `status`
- `sponsor_class`
- `age_group`
- `country`
- `year`
- `q`
- `page`
- `page_size`

Returns:

- paginated trial cards
- applied filters
- match explanations

### `GET /api/v1/trials/{nct_id}`

Returns the normalized full record and chunked evidence sections for one trial.

### `POST /api/v1/compare`

Request body:

- `nct_ids`: array of 2 to 5 NCT IDs

Returns:

- side-by-side comparison of status, phase, sponsor, interventions, eligibility, outcomes, dates, and locations

### `POST /api/v1/ask`

Request body:

- `question`
- `filters`
- `nct_ids` optional

Returns:

- grounded answer
- cited trial IDs
- cited field paths or chunk IDs
- uncertainty notes

### `POST /api/v1/ingest/run`

Admin-only ingestion trigger for local development.

## Starter repo layout

```text
Rag Project/
├── README.md
├── docs/
│   ├── architecture.md
│   └── schema-and-api.md
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── public/
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   ├── core/
│       │   ├── db/
│       │   ├── models/
│       │   ├── schemas/
│       │   └── services/
│       └── tests/
├── packages/
│   ├── shared-types/
│   └── ui/
├── data/
│   ├── raw/
│   └── normalized/
└── scripts/
    ├── ingest_trials.py
    ├── normalize_trials.py
    └── build_eval_set.py
```

## Build order

1. Implement the normalized schema and ingestion pipeline
2. Build structured filtering over stored records
3. Add lexical retrieval over key fields and chunks
4. Add embeddings and semantic retrieval
5. Add compare and ask endpoints
6. Build the web UI over the stable API
7. Add evaluation before tuning prompts
