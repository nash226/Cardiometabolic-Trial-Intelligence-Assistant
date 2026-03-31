from __future__ import annotations

from pydantic import BaseModel


class TrialCondition(BaseModel):
    name: str
    normalized_name: str | None = None
    is_primary: bool


class TrialIntervention(BaseModel):
    intervention_type: str | None = None
    name: str
    normalized_name: str | None = None
    description: str | None = None
    arm_group_labels: list[str]
    drug_class: str | None = None


class TrialArm(BaseModel):
    label: str | None = None
    type: str | None = None
    description: str | None = None
    intervention_names: list[str]


class TrialOutcome(BaseModel):
    outcome_type: str | None = None
    measure: str | None = None
    description: str | None = None
    time_frame: str | None = None


class TrialLocation(BaseModel):
    facility_name: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    status: str | None = None


class TrialEligibility(BaseModel):
    criteria_text: str | None = None
    sex: str | None = None
    minimum_age_text: str | None = None
    maximum_age_text: str | None = None
    age_groups: list[str]
    healthy_volunteers: bool | None = None


class TrialValidation(BaseModel):
    accepted: bool
    errors: list[str]
    rejection_reasons: list[str]
    warning_reasons: list[str]


class TrialChunkPreview(BaseModel):
    chunk_id: str
    chunk_type: str
    title: str | None = None
    snippet: str
    source_field_paths: list[str]


class TrialDetail(BaseModel):
    nct_id: str
    source: str
    source_url: str | None = None
    brief_title: str
    official_title: str | None = None
    brief_summary: str | None = None
    detailed_description: str | None = None
    study_type: str | None = None
    phases: list[str]
    allocation: str | None = None
    intervention_model: str | None = None
    masking: str | None = None
    primary_purpose: str | None = None
    enrollment_count: int | None = None
    enrollment_type: str | None = None
    overall_status: str | None = None
    last_known_status: str | None = None
    start_date_text: str | None = None
    primary_completion_date_text: str | None = None
    completion_date_text: str | None = None
    study_first_posted_at_text: str | None = None
    results_first_posted_at_text: str | None = None
    last_update_posted_at_text: str | None = None
    is_2026_relevant: bool
    relevance_reasons: list[str]
    lead_sponsor_name: str | None = None
    lead_sponsor_class: str | None = None
    collaborator_names: list[str]
    sex: str | None = None
    minimum_age_text: str | None = None
    maximum_age_text: str | None = None
    age_groups: list[str]
    healthy_volunteers: bool | None = None
    condition_labels: list[str]
    intervention_labels: list[str]
    drug_class_labels: list[str]
    keyword_labels: list[str]
    country_codes: list[str]
    has_us_sites: bool
    raw_has_results: bool | None = None
    conditions: list[TrialCondition]
    interventions: list[TrialIntervention]
    arms: list[TrialArm]
    outcomes: list[TrialOutcome]
    locations: list[TrialLocation]
    eligibility: TrialEligibility | None = None
    validation: TrialValidation | None = None
    chunks: list[TrialChunkPreview]
