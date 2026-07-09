# Normalizer

This is the second ingestion layer.

The normalizer takes one raw ClinicalTrials.gov study record and maps it into a simpler internal structure that matches our schema design.

## Script

- [scripts/normalize_trial.py](../scripts/normalize_trial.py)

## What it does

Input:

- one raw study JSON file from [data/raw](../data/raw)

Output:

- one normalized JSON file in [data/normalized](../data/normalized)

The normalized payload currently contains:

- `trial`: top-level scalar fields
- `conditions`: normalized condition rows
- `interventions`: normalized intervention rows
- `arms`: arm groups
- `outcomes`: primary and secondary outcomes
- `locations`: site locations
- `eligibility`: preserved eligibility fields

This is intentionally file-to-file, not database-backed. The goal is to make raw vs normalized comparison easy.

## What it derives

The script already derives a few helper fields because they are part of ingestion, not presentation:

- `source_url`
- `is_2026_relevant`
- `relevance_reasons`
- `condition_labels`
- `drug_class_labels`
- `has_us_sites`

## What it does not do yet

- strict validation and rejection logging
- perfect condition taxonomy normalization
- robust partial-date parsing
- chunk generation
- storage in Postgres

## Example usage

Normalize one fetched study:

```bash
python3 scripts/normalize_trial.py \
  data/raw/<timestamp>/studies/<NCT_ID>.json
```

Write to a custom output path:

```bash
python3 scripts/normalize_trial.py \
  data/raw/<timestamp>/studies/<NCT_ID>.json \
  --output-path data/normalized/example.json
```

## How to inspect the result

Open the normalized file:

```bash
python3 -m json.tool data/normalized/<NCT_ID>.json | less
```

The learning exercise is:

1. open the raw file
2. open the normalized file
3. verify how each source module turned into the normalized shape

Questions to ask while comparing:

- which fields copied directly?
- which fields became arrays of child objects?
- which fields were derived?
- which raw fields did we intentionally ignore for now?

## Why this stage matters

This is the first point where our application gets its own opinionated data model.

That matters because everything downstream depends on it:

- filtering
- comparison
- retrieval chunking
- citations
- answer synthesis

If this layer is clear and inspectable, the rest of the system becomes much easier to reason about.
