# Fused Search

Fused search combines:

- structured trial filtering
- lexical chunk scoring
- semantic chunk scoring

into one ranked result set.

## Script

- [scripts/fused_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/fused_search.py)

## Why this matters

This is the first retrieval layer that treats lexical and semantic search as complementary signals instead of separate modes.

## Current flow

1. select eligible trials using structured filters
2. compute lexical scores on chunks from those trials
3. compute semantic scores on chunks from those trials
4. min-max normalize each score family
5. combine them with configurable weights

## Output fields

Each result includes:

- `chunk_id`
- `trial_nct_id`
- `chunk_type`
- `title`
- `snippet`
- `lexical_score_raw`
- `semantic_score_raw`
- `lexical_score_norm`
- `semantic_score_norm`
- `fused_score`
- `source_field_paths`

## Example usage

```bash
python3 scripts/fused_search.py "incretin obesity therapy" \
  --condition obesity \
  --accepted-only \
  --study-type INTERVENTIONAL \
  --year-2026-only \
  --semantic-provider openai \
  --lexical-weight 0.4 \
  --semantic-weight 0.6
```

## Why score transparency matters

The fused layer reports lexical and semantic scores separately so we can inspect:

- which signal is actually driving a result
- whether the current weighting is sensible
- whether semantic search is adding value or only noise
