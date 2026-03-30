# Validation

Validation is the ingestion stage that decides whether a normalized record belongs in the MVP corpus.

## Script

- [scripts/validate_trial.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/validate_trial.py)

## Why this exists

Normalization and validation are not the same thing.

- normalization answers: `what does this source record become in our system?`
- validation answers: `should this normalized record enter the corpus?`

A record can be normalized successfully and still be rejected as:

- out of scope
- missing required identity fields
- missing usable phase information

## Current validation rules

### Required fields

These must exist:

- `nct_id`
- `brief_title`
- `study_type`
- `overall_status`

### Rejection rules

The record is rejected if:

- `study_type` is not `INTERVENTIONAL`
- phases are missing
- phases do not overlap with `PHASE2`, `PHASE3`, or `PHASE4`
- normalized condition labels are missing
- normalized condition labels do not overlap with `obesity`, `type_2_diabetes`, or `mash`

### Warning rules

The record is still accepted, but warnings are added if these are missing:

- `official_title`
- `brief_summary`
- `criteria_text`
- locations
- outcomes

## Example usage

```bash
python3 scripts/validate_trial.py \
  data/normalized/<NCT_ID>.json
```

This writes a validation result to:

- [data/normalized/validation](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/normalized/validation)

## Validation output

The result includes:

- `accepted`
- `errors`
- `rejection_reasons`
- `warning_reasons`
- a small summary block for quick inspection

## Why this is useful as a learning step

Validation is where product scope becomes code rules.

It forces us to define:

- what counts as in-scope
- what counts as required
- what counts as optional but useful

That makes the corpus construction logic explicit instead of accidental.
