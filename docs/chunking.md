# Chunking

Chunking is the ingestion layer that converts a normalized trial record into retrieval-ready evidence units.

## Script

- [scripts/generate_chunks.py](../scripts/generate_chunks.py)

## Why this exists

Normalized records are easier to work with than raw source JSON, but they are still too large and too mixed for good retrieval.

We do not want to retrieve:

- one giant trial blob

We also do not want random fixed-size text windows that mix unrelated fields.

Instead, we want field-aware chunks that preserve the meaning of each trial section.

## Current chunk types

- `status_identity`
- `conditions_interventions`
- `summary_description`
- `eligibility`
- `outcomes`
- `timeline`
- `sponsor_locations`

These follow the chunking strategy defined in [docs/architecture.md](../docs/architecture.md).

## Output shape

Each chunk includes:

- `chunk_id`
- `trial_nct_id`
- `chunk_type`
- `title`
- `content`
- `source_field_paths`
- `token_count_estimate`

The `source_field_paths` field is especially important because it preserves traceability for citations and debugging.

## Example usage

```bash
python3 scripts/generate_chunks.py \
  data/processed_runs/20260330T021936Z/normalized/NCT06893016.json
```

This writes a chunk file to:

- [data/chunks](../data/chunks)

When used through the batch pipeline, chunk files are written under each processed run:

- [data/processed_runs](../data/processed_runs)

## Design notes

### Field-aware instead of fixed windows

This project uses section-based chunking because trial records are semi-structured.

That improves:

- retrieval precision
- citation clarity
- explainability

### Location sampling

Some studies have very large location arrays.

For now, the `sponsor_locations` chunk includes only a location sample instead of every location line.

This keeps the chunk useful without allowing very large site lists to dominate retrieval content.

### Outcome grouping

Outcomes currently stay in one chunk, which is acceptable for the current MVP stage.

If we later see very large outcome lists causing retrieval noise, we can split them into multiple chunks.
