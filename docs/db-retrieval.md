# DB Retrieval

This is the first retrieval layer that queries the stored Postgres corpus directly instead of reading JSON artifacts.

## Script

- [scripts/db_hybrid_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/db_hybrid_search.py)

## What it does

The script combines:

- structured trial filtering from `trials` and `trial_validation`
- lexical chunk search from `trial_chunks.content_tsv`

## Why this matters

At this point, the file-based pipeline has already proven the retrieval design.

DB-backed retrieval is the transition from:

- prototype artifact search

to:

- real backend query behavior

## Current SQL approach

1. select eligible trials using structured metadata filters
2. join eligible trials to `trial_chunks`
3. use `websearch_to_tsquery` and `ts_rank_cd` for lexical chunk ranking
4. return chunk-level hits with trial IDs and field-path metadata

## Example usage

```bash
python3 scripts/db_hybrid_search.py "primary completion" \
  --condition obesity \
  --phase PHASE3 \
  --study-type INTERVENTIONAL \
  --accepted-only \
  --year-2026-only
```

## Next likely extension

After this lexical DB layer is verified, the next DB-backed retrieval step should be:

- semantic vector search from `trial_chunks.embedding`

and then:

- fused DB retrieval

That next semantic layer is now implemented in:

- [scripts/db_semantic_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/db_semantic_search.py)
