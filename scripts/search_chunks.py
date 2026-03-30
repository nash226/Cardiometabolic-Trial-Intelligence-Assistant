#!/usr/bin/env python3
"""Run simple lexical search over the chunk index."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9_+-]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search the lexical chunk index."
    )
    parser.add_argument("query", help="Search query.")
    parser.add_argument(
        "--index-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_lexical_index.json",
        help="Path to the lexical index JSON file.",
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


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def make_snippet(content: str, query_terms: list[str], snippet_len: int = 180) -> str:
    lowered = content.lower()
    start = 0
    for term in query_terms:
        idx = lowered.find(term.lower())
        if idx != -1:
            start = max(0, idx - 40)
            break
    snippet = content[start : start + snippet_len].replace("\n", " ")
    return snippet.strip()


def search_index(index: dict[str, Any], query: str, limit: int) -> list[dict[str, Any]]:
    query_tokens = tokenize(query)
    postings = index.get("postings", {})
    chunk_store = index.get("chunk_store", {})
    scores: dict[str, float] = {}

    for token in query_tokens:
        token_postings = postings.get(token, {})
        for chunk_id, count in token_postings.items():
            scores[chunk_id] = scores.get(chunk_id, 0.0) + float(count)

    normalized_query = " ".join(query_tokens)
    for chunk_id, chunk in chunk_store.items():
        content = chunk.get("content", "")
        if normalized_query and normalized_query in content.lower():
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 3.0

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
    results = []
    for chunk_id, score in ranked:
        chunk = chunk_store[chunk_id]
        results.append(
            {
                "score": score,
                "chunk_id": chunk["chunk_id"],
                "trial_nct_id": chunk.get("trial_nct_id"),
                "chunk_type": chunk.get("chunk_type"),
                "title": chunk.get("title"),
                "snippet": make_snippet(chunk.get("content", ""), query_tokens),
                "source_field_paths": chunk.get("source_field_paths", []),
            }
        )
    return results


def main() -> int:
    args = parse_args()
    index = load_json(args.index_path)
    results = search_index(index, args.query, args.limit)
    print(json.dumps({"query": args.query, "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
