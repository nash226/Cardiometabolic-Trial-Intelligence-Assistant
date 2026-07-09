# Condition Taxonomy

Condition taxonomy is the ingestion layer that maps raw study condition strings into stable internal condition labels.

## Why this exists

Raw ClinicalTrials.gov condition strings are not standardized enough for reliable filtering by themselves.

Examples:

- `Type 2 Diabetes`
- `Type 2 Diabetes Mellitus`
- `Child Obesity`
- `Obesity and Obesity-related Medical Conditions`
- `MASH`
- `NAFLD`

These should map into a smaller set of stable labels for the MVP.

## Current files

- [scripts/lib/condition_taxonomy.py](../scripts/lib/condition_taxonomy.py)
- [scripts/lib/condition_taxonomy.json](../scripts/lib/condition_taxonomy.json)

## Current normalized labels

- `obesity`
- `type_2_diabetes`
- `mash`

## How it works

The taxonomy currently uses two strategies:

1. explicit mappings for known source labels
2. simple contains-rules for broader term matching

That gives us:

- transparency
- deterministic behavior
- easy local edits

## Why this is better than inline heuristics

Moving taxonomy out of the normalizer makes it easier to:

- inspect the mapping rules directly
- update terminology without touching unrelated normalization code
- expand the taxonomy carefully over time

## Current limitation

This is still a lightweight rule-based taxonomy.

It does not yet:

- use synonyms from an external terminology source
- distinguish nuanced disease overlap cases automatically
- infer scope from keyword fields alone

That is acceptable for the current MVP as long as we keep the mappings explicit and conservative.
