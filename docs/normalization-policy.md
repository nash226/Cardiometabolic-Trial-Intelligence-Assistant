# Normalization Policy

This document defines what normalization is allowed to do in this project.

The goal is to keep normalization:

- deterministic
- source-grounded
- easy to audit
- useful for downstream retrieval and filtering

## 1. Core identity rules

The normalizer must preserve stable study identity.

Rules:

- `nct_id` must come directly from the source record
- `brief_title` must be preserved as source text
- `official_title` is optional and must never be invented
- `source_url` may be derived deterministically from `nct_id`

Rationale:

- identity fields anchor every downstream join, citation, and compare view

## 2. Source fidelity rules

Normalization must preserve important source text rather than rewriting it.

Fields to preserve as source text:

- `brief_summary`
- `detailed_description`
- `criteria_text`
- outcome measure text
- outcome descriptions

Rationale:

- retrieval and citations depend on exact source text
- summarization belongs later in the system, not in ingestion

## 3. Internal naming rules

Internal field names should use one consistent convention.

Rules:

- use `snake_case` for normalized field names
- source field names should not leak into the internal schema unless necessary for traceability

Rationale:

- consistent naming reduces confusion across scripts, schemas, and database models

## 4. Repeated-field rules

Repeated source fields must become repeated normalized structures.

Rules:

- single-value study fields stay on the top-level `trial` object
- repeated source arrays become child collections

Expected child collections:

- `conditions`
- `interventions`
- `arms`
- `outcomes`
- `locations`
- `eligibility` remains a grouped object because it is conceptually one section

Rationale:

- flattening repeated data into strings would weaken filtering, comparison, and retrieval

## 5. Condition normalization rules

Conditions need both source fidelity and normalized grouping.

Rules:

- preserve the raw condition string
- derive a normalized label when the mapping is clear
- normalized condition labels should support stable filtering
- if the condition is ambiguous, keep the raw string and leave the normalized label blank

Current high-level normalized labels:

- `obesity`
- `type_2_diabetes`
- `mash`

Rationale:

- raw labels support fidelity
- normalized labels support filtering and evaluation

## 6. Intervention normalization rules

Interventions should remain exact at the source level and conservative at the helper-field level.

Rules:

- preserve the exact intervention name
- store a normalized helper version for matching if useful
- derive `drug_class` only when the mapping is explicit and explainable
- if the intervention class is uncertain, leave it blank

Rationale:

- intervention-family queries matter, but weak inference would pollute retrieval quality

## 7. Date handling rules

Dates should preserve source truth over fake precision.

Rules:

- keep source date strings as provided when available
- normalize dates only when the source precision supports it
- do not silently invent missing days or months

Rationale:

- trial dates drive 2026 relevance and comparison logic
- fake precision would create misleading downstream behavior

## 8. Missing-data rules

Missing fields should remain explicit.

Rules:

- use `null` or empty arrays for missing optional fields
- do not guess missing values
- do not backfill fields from unrelated source text

Rationale:

- explicit missingness is safer than hidden assumptions

## 9. Enum and boolean rules

Enums and booleans should be normalized into stable internal values when possible.

Examples:

- `overall_status`
- `sex`
- `healthy_volunteers`
- `phases`

Rules:

- preserve the source meaning
- keep mappings deterministic
- avoid collapsing distinct source categories into one label unless that collapse is intentional

Rationale:

- stable enums simplify filtering and comparisons

## 10. Derived-field rules

Normalization may create a small set of helper fields, but only when the derivation is deterministic and explainable.

Currently allowed derived fields:

- `source_url`
- `is_2026_relevant`
- `relevance_reasons`
- `condition_labels`
- `drug_class_labels`
- `has_us_sites`

Rules:

- derived fields must come from source data plus simple local rules
- derived fields must not depend on LLM inference
- derived fields should be explainable in documentation or code comments

Rationale:

- helper fields can improve retrieval and filtering without reducing auditability

## 11. No-LLM rule

Normalization must not call an LLM.

Rules:

- no AI summarization
- no generative tagging
- no free-form inference

Rationale:

- normalization should be deterministic, reproducible, and easy to debug

## 12. Determinism rule

The same input record should always produce the same normalized output.

Rules:

- no randomness
- no time-dependent normalization behavior
- no external model calls

Rationale:

- deterministic ETL is essential for debugging, tests, and evaluation

## 13. Cleaning rules

Normalization may apply only shallow cleanup.

Allowed cleanup:

- trim whitespace
- normalize repeated spacing
- normalize helper-field casing when needed

Not allowed:

- rewriting narrative source text
- paraphrasing
- dropping meaning-bearing content

Rationale:

- we want consistency without losing source fidelity

## 14. Traceability rule

Every normalized field should be traceable to:

- a source field path
- or a simple deterministic derivation rule

Rationale:

- if we cannot explain where a field came from, it does not belong in normalization

## 15. Relationship to validation

Normalization and validation are separate concerns.

- normalization answers: `what does the source record become in our system?`
- validation answers: `should this record be accepted into the corpus?`

This matters because a record can be:

- successfully normalized
- but still rejected as out of scope

That separation should remain explicit in the codebase.
