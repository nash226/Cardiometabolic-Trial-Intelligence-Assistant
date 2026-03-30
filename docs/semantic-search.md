# Semantic Search

Semantic search is the retrieval layer that ranks chunks by embedding similarity instead of exact keyword overlap.

## Scripts

- [scripts/build_chunk_embeddings.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/build_chunk_embeddings.py)
- [scripts/semantic_search.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/semantic_search.py)
- [scripts/lib/embedding_utils.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/lib/embedding_utils.py)

## Provider strategy

The semantic layer currently supports two providers:

- `local_debug`
- `openai`

### `local_debug`

This is a deterministic local hashed embedding.

Why it exists:

- works offline
- useful for development and architecture testing
- lets us build the semantic retrieval layer without blocking on external APIs

Important limitation:

- it is not a true production semantic model

### `openai`

This uses the OpenAI embeddings API when:

- network access is available
- `OPENAI_API_KEY` is set
- a model name is provided

Why this matters:

- it gives us a path to real semantic retrieval without changing the surrounding architecture

## Why semantic search comes after hybrid lexical retrieval

We wanted a baseline first:

- chunking
- lexical search
- structured + lexical search

That baseline makes semantic improvements easier to evaluate later.

## Example workflow

Build a local debug semantic index:

```bash
python3 scripts/build_chunk_embeddings.py \
  data/processed_runs_with_chunks/20260330T021936Z/chunks \
  --provider local_debug
```

Search it:

```bash
python3 scripts/semantic_search.py "incretin obesity therapy"
```

## Current limitation

Until we run the `openai` provider with a real embedding model, this layer should be treated as:

- architecture-complete
- quality-incomplete

That is intentional for now.
