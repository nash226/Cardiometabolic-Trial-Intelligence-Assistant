# Hybrid Search

Hybrid search combines:

- structured trial filters
- lexical chunk search

## Script

- [scripts/hybrid_search.py](../scripts/hybrid_search.py)

## Why this matters

Lexical search alone only answers:

- which chunks contain these words?

Hybrid retrieval answers:

- which chunks contain these words from trials that also satisfy the requested metadata constraints?

That is much closer to real product questions.

## Current structured filters

- `condition`
- `phase`
- `study_type`
- `accepted_only`
- `year_2026_only`

## Current retrieval flow

1. read the processed run summary
2. identify eligible trials from structured filters
3. run lexical scoring only over chunks from those trials
4. return chunk-level hits with trial metadata

## Example usage

```bash
python3 scripts/hybrid_search.py "GLP-1" \
  --condition type_2_diabetes \
  --study-type INTERVENTIONAL \
  --accepted-only \
  --year-2026-only
```

```bash
python3 scripts/hybrid_search.py "primary completion" \
  --condition obesity \
  --phase PHASE3 \
  --accepted-only
```

## Why this comes before embeddings

This gives us a clear hybrid baseline before semantic retrieval:

- structured constraints control corpus eligibility
- lexical search ranks evidence within the eligible set

That makes later embedding-based improvements easier to evaluate.
