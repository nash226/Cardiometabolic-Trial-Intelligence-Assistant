#!/usr/bin/env python3
"""Run semantic search over the chunk embeddings index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lib.embedding_utils import cosine_similarity, embed_text
from search_chunks import make_snippet, tokenize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search the semantic chunk index."
    )
    parser.add_argument("query", help="Semantic query text.")
    parser.add_argument(
        "--index-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_semantic_index.json",
        help="Path to the semantic index JSON file.",
    )
    parser.add_argument(
        "--provider",
        choices=["local_debug", "openai"],
        help="Override embedding provider. Defaults to the provider stored in the index.",
    )
    parser.add_argument(
        "--model",
        help="Embedding model override. Needed with provider=openai if not stored in the index.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of hits to return.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_search(index: dict[str, Any], query: str, provider: str, model: str | None, limit: int) -> list[dict[str, Any]]:
    query_embedding = embed_text(query, provider=provider, model=model)
    chunk_store = index.get("chunk_store", {})
    embeddings = index.get("embeddings", {})
    ranked: list[tuple[str, float]] = []

    for chunk_id, vector in embeddings.items():
        if not isinstance(vector, list):
            continue
        score = cosine_similarity(query_embedding, [float(value) for value in vector])
        ranked.append((chunk_id, score))

    ranked.sort(key=lambda item: (-item[1], item[0]))
    results = []
    for chunk_id, score in ranked[:limit]:
        chunk = chunk_store[chunk_id]
        results.append(
            {
                "score": score,
                "chunk_id": chunk["chunk_id"],
                "trial_nct_id": chunk.get("trial_nct_id"),
                "chunk_type": chunk.get("chunk_type"),
                "title": chunk.get("title"),
                "snippet": make_snippet(chunk.get("content", ""), tokenize(query)),
                "source_field_paths": chunk.get("source_field_paths", []),
            }
        )
    return results


def main() -> int:
    args = parse_args()
    index = load_json(args.index_path)
    provider = args.provider or index.get("provider") or "local_debug"
    model = args.model or index.get("model")
    results = semantic_search(index, args.query, provider=provider, model=model, limit=args.limit)
    print(
        json.dumps(
            {
                "query": args.query,
                "provider": provider,
                "model": model,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
