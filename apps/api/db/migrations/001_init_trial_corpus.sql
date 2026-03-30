CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS trials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nct_id TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    source_url TEXT,
    brief_title TEXT NOT NULL,
    official_title TEXT,
    brief_summary TEXT,
    detailed_description TEXT,
    study_type TEXT,
    phases TEXT[] NOT NULL DEFAULT '{}',
    allocation TEXT,
    intervention_model TEXT,
    masking TEXT,
    primary_purpose TEXT,
    enrollment_count INTEGER,
    enrollment_type TEXT,
    overall_status TEXT,
    last_known_status TEXT,
    start_date_text TEXT,
    primary_completion_date_text TEXT,
    completion_date_text TEXT,
    study_first_posted_at_text TEXT,
    results_first_posted_at_text TEXT,
    last_update_posted_at_text TEXT,
    is_2026_relevant BOOLEAN NOT NULL DEFAULT FALSE,
    relevance_reasons TEXT[] NOT NULL DEFAULT '{}',
    lead_sponsor_name TEXT,
    lead_sponsor_class TEXT,
    collaborator_names TEXT[] NOT NULL DEFAULT '{}',
    sex TEXT,
    minimum_age_text TEXT,
    maximum_age_text TEXT,
    age_groups TEXT[] NOT NULL DEFAULT '{}',
    healthy_volunteers BOOLEAN,
    condition_labels TEXT[] NOT NULL DEFAULT '{}',
    intervention_labels TEXT[] NOT NULL DEFAULT '{}',
    drug_class_labels TEXT[] NOT NULL DEFAULT '{}',
    keyword_labels TEXT[] NOT NULL DEFAULT '{}',
    country_codes TEXT[] NOT NULL DEFAULT '{}',
    has_us_sites BOOLEAN NOT NULL DEFAULT FALSE,
    raw_has_results BOOLEAN,
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trial_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    normalized_name TEXT,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS trial_interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    intervention_type TEXT,
    name TEXT NOT NULL,
    normalized_name TEXT,
    description TEXT,
    arm_group_labels TEXT[] NOT NULL DEFAULT '{}',
    drug_class TEXT
);

CREATE TABLE IF NOT EXISTS trial_arms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    label TEXT,
    type TEXT,
    description TEXT,
    intervention_names TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS trial_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    outcome_type TEXT,
    measure TEXT,
    description TEXT,
    time_frame TEXT
);

CREATE TABLE IF NOT EXISTS trial_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    facility_name TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS trial_eligibility (
    trial_id UUID PRIMARY KEY REFERENCES trials(id) ON DELETE CASCADE,
    criteria_text TEXT,
    sex TEXT,
    minimum_age_text TEXT,
    maximum_age_text TEXT,
    age_groups TEXT[] NOT NULL DEFAULT '{}',
    healthy_volunteers BOOLEAN
);

CREATE TABLE IF NOT EXISTS trial_validation (
    trial_id UUID PRIMARY KEY REFERENCES trials(id) ON DELETE CASCADE,
    accepted BOOLEAN NOT NULL,
    errors TEXT[] NOT NULL DEFAULT '{}',
    rejection_reasons TEXT[] NOT NULL DEFAULT '{}',
    warning_reasons TEXT[] NOT NULL DEFAULT '{}',
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trial_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id TEXT NOT NULL UNIQUE,
    trial_id UUID NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    trial_nct_id TEXT NOT NULL,
    chunk_type TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    source_field_paths TEXT[] NOT NULL DEFAULT '{}',
    token_count_estimate INTEGER,
    content_tsv tsvector,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trials_condition_labels ON trials USING GIN (condition_labels);
CREATE INDEX IF NOT EXISTS idx_trials_phases ON trials USING GIN (phases);
CREATE INDEX IF NOT EXISTS idx_trials_relevance_reasons ON trials USING GIN (relevance_reasons);
CREATE INDEX IF NOT EXISTS idx_trials_overall_status ON trials (overall_status);
CREATE INDEX IF NOT EXISTS idx_trials_study_type ON trials (study_type);
CREATE INDEX IF NOT EXISTS idx_trials_is_2026_relevant ON trials (is_2026_relevant);

CREATE INDEX IF NOT EXISTS idx_trial_conditions_trial_id ON trial_conditions (trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_interventions_trial_id ON trial_interventions (trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_arms_trial_id ON trial_arms (trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_outcomes_trial_id ON trial_outcomes (trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_locations_trial_id ON trial_locations (trial_id);

CREATE INDEX IF NOT EXISTS idx_trial_validation_accepted ON trial_validation (accepted);

CREATE INDEX IF NOT EXISTS idx_trial_chunks_trial_id ON trial_chunks (trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_chunks_chunk_type ON trial_chunks (chunk_type);
CREATE INDEX IF NOT EXISTS idx_trial_chunks_content_tsv ON trial_chunks USING GIN (content_tsv);
