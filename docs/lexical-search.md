# Lexical Search

This is the first retrieval layer over the chunked corpus.

## Scripts

- [scripts/build_chunk_index.py](../scripts/build_chunk_index.py)
- [scripts/search_chunks.py](../scripts/search_chunks.py)

## What it does

The lexical retrieval layer:

- reads chunk files
- tokenizes chunk content
- builds an inverted index
- returns chunk-level matches for keyword queries

## Why lexical search first

Lexical search is the right first retrieval layer because it is:

- easy to inspect
- easy to debug
- effective for exact terms like drug names, phases, sponsor names, and endpoint phrases

This lets us evaluate retrieval behavior before adding embeddings.

## Index contents

The current index stores:

- postings from token to chunk IDs and term counts
- chunk metadata for each chunk

That metadata includes:

- `chunk_id`
- `trial_nct_id`
- `chunk_type`
- `title`
- `content`
- `source_field_paths`

## Search output

The search script returns:

- `score`
- `chunk_id`
- `trial_nct_id`
- `chunk_type`
- `title`
- `snippet`
- `source_field_paths`

## Example workflow

Build an index for one processed run:

```bash
python3 scripts/build_chunk_index.py \
  data/processed_runs_with_chunks/20260330T021936Z/chunks
```

Search it:

```bash
python3 scripts/search_chunks.py "type 2 diabetes"
python3 scripts/search_chunks.py "primary completion"
python3 scripts/search_chunks.py "GLP-1"
```

## Current limitations

- scoring is intentionally simple
- there is no stemming or synonym expansion
- results are chunk-level only
- no structured filters are combined yet

That is acceptable for the first retrieval layer because the main goal is transparency and inspectability.
