# DB Fused Retrieval

This is the database-backed version of fused retrieval.

## Script

- [scripts/db_fused_search.py](../scripts/db_fused_search.py)

## What it does

The script combines:

- structured trial filters from Postgres
- lexical scores from `trial_chunks.content_tsv`
- semantic scores from `trial_chunks.embedding`
- query-aware chunk-type weighting

and returns a fused ranking.

## Why this matters

This is the point where the retrieval stack is fully operating from the persistent corpus instead of the file artifacts.

## Output transparency

Each result includes:

- chunk type weight
- lexical raw score
- semantic raw score
- lexical normalized score
- semantic normalized score
- fused score

That keeps ranking behavior explainable.
