#!/usr/bin/env python3
"""Fuse structured filtering, lexical search, and semantic search into one ranked result set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from hybrid_search import eligible_trial_ids
from search_chunks import load_json as load_index_json
from search_chunks import make_snippet, tokenize
from semantic_search import semantic_search


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run fused retrieval over lexical and semantic chunk indexes."
    )
    parser.add_argument("query", help="Search query text.")
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=Path("data") / "processed_runs_with_chunks" / "20260330T021936Z" / "summary.json",
        help="Path to a processed run summary.json file.",
    )
    parser.add_argument(
        "--lexical-index-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_lexical_index.json",
        help="Path to the lexical index JSON file.",
    )
    parser.add_argument(
        "--semantic-index-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_semantic_index.json",
        help="Path to the semantic index JSON file.",
    )
    parser.add_argument("--condition", help="Filter by normalized condition label.")
    parser.add_argument("--phase", help="Filter by phase, for example PHASE3.")
    parser.add_argument("--study-type", help="Filter by study type, for example INTERVENTIONAL.")
    parser.add_argument("--accepted-only", action="store_true", help="Limit to accepted trials.")
    parser.add_argument("--year-2026-only", action="store_true", help="Limit to 2026-relevant trials.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of hits to return.")
    parser.add_argument("--lexical-weight", type=float, default=0.5, help="Weight for lexical score.")
    parser.add_argument("--semantic-weight", type=float, default=0.5, help="Weight for semantic score.")
    parser.add_argument(
        "--semantic-provider",
        choices=["local_debug", "openai"],
        help="Override semantic provider. Defaults to provider stored in semantic index.",
    )
    parser.add_argument("--semantic-model", help="Override semantic model if needed.")
    return parser.parse_args()


def lexical_scores(index: dict[str, Any], allowed_trial_ids: set[str], query: str) -> dict[str, float]:
    query_tokens = tokenize(query)
    postings = index.get("postings", {})
    chunk_store = index.get("chunk_store", {})
    scores: dict[str, float] = {}

    for token in query_tokens:
        token_postings = postings.get(token, {})
        for chunk_id, count in token_postings.items():
            chunk = chunk_store.get(chunk_id, {})
            if chunk.get("trial_nct_id") not in allowed_trial_ids:
                continue
            scores[chunk_id] = scores.get(chunk_id, 0.0) + float(count)

    normalized_query = " ".join(query_tokens)
    for chunk_id in list(scores.keys()):
        chunk = chunk_store[chunk_id]
        content = chunk.get("content", "")
        if normalized_query and normalized_query in content.lower():
            scores[chunk_id] += 3.0
    return scores


def semantic_scores(index: dict[str, Any], allowed_trial_ids: set[str], query: str, provider: str, model: str | None) -> dict[str, float]:
    results = semantic_search(index, query, provider=provider, model=model, limit=index.get("chunk_count", 0))
    scores: dict[str, float] = {}
    for result in results:
        chunk_id = result["chunk_id"]
        if result.get("trial_nct_id") not in allowed_trial_ids:
            continue
        scores[chunk_id] = float(result["score"])
    return scores


def normalize_score_map(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    values = list(scores.values())
    min_score = min(values)
    max_score = max(values)
    if max_score == min_score:
        return {key: 1.0 for key in scores}
    return {key: (value - min_score) / (max_score - min_score) for key, value in scores.items()}


def fused_results(
    lexical_index: dict[str, Any],
    semantic_index: dict[str, Any],
    allowed_trial_ids: set[str],
    query: str,
    *,
    lexical_weight: float,
    semantic_weight: float,
    semantic_provider: str,
    semantic_model: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    raw_lexical = lexical_scores(lexical_index, allowed_trial_ids, query)
    raw_semantic = semantic_scores(
        semantic_index,
        allowed_trial_ids,
        query,
        provider=semantic_provider,
        model=semantic_model,
    )

    norm_lexical = normalize_score_map(raw_lexical)
    norm_semantic = normalize_score_map(raw_semantic)
    chunk_store = lexical_index.get("chunk_store", {})

    all_chunk_ids = set(norm_lexical) | set(norm_semantic)
    ranked: list[tuple[str, float]] = []
    for chunk_id in all_chunk_ids:
        fused = (lexical_weight * norm_lexical.get(chunk_id, 0.0)) + (
            semantic_weight * norm_semantic.get(chunk_id, 0.0)
        )
        ranked.append((chunk_id, fused))

    ranked.sort(key=lambda item: (-item[1], item[0]))
    results: list[dict[str, Any]] = []
    for chunk_id, fused_score in ranked[:limit]:
        chunk = chunk_store.get(chunk_id) or semantic_index.get("chunk_store", {}).get(chunk_id, {})
        results.append(
            {
                "chunk_id": chunk_id,
                "trial_nct_id": chunk.get("trial_nct_id"),
                "chunk_type": chunk.get("chunk_type"),
                "title": chunk.get("title"),
                "snippet": make_snippet(chunk.get("content", ""), tokenize(query)),
                "lexical_score_raw": raw_lexical.get(chunk_id, 0.0),
                "semantic_score_raw": raw_semantic.get(chunk_id, 0.0),
                "lexical_score_norm": norm_lexical.get(chunk_id, 0.0),
                "semantic_score_norm": norm_semantic.get(chunk_id, 0.0),
                "fused_score": fused_score,
                "source_field_paths": chunk.get("source_field_paths", []),
            }
        )
    return results


def main() -> int:
    args = parse_args()
    summary_payload = load_index_json(args.summary_path)
    lexical_index = load_index_json(args.lexical_index_path)
    semantic_index = load_index_json(args.semantic_index_path)
    allowed_trial_ids = eligible_trial_ids(summary_payload, args)

    semantic_provider = args.semantic_provider or semantic_index.get("provider") or "local_debug"
    semantic_model = args.semantic_model or semantic_index.get("model")

    results = fused_results(
        lexical_index,
        semantic_index,
        allowed_trial_ids,
        args.query,
        lexical_weight=args.lexical_weight,
        semantic_weight=args.semantic_weight,
        semantic_provider=semantic_provider,
        semantic_model=semantic_model,
        limit=args.limit,
    )

    print(
        json.dumps(
            {
                "query": args.query,
                "filters": {
                    "condition": args.condition,
                    "phase": args.phase,
                    "study_type": args.study_type,
                    "accepted_only": args.accepted_only,
                    "year_2026_only": args.year_2026_only,
                },
                "weights": {
                    "lexical": args.lexical_weight,
                    "semantic": args.semantic_weight,
                },
                "eligible_trial_count": len(allowed_trial_ids),
                "semantic_provider": semantic_provider,
                "semantic_model": semantic_model,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
