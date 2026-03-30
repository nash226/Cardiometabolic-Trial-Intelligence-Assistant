#!/usr/bin/env python3
"""Run structured + lexical search over a processed trial run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from search_chunks import load_json as load_index_json
from search_chunks import make_snippet, tokenize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search chunks using structured trial filters plus lexical matching."
    )
    parser.add_argument("query", help="Lexical query string.")
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=Path("data") / "processed_runs_with_chunks" / "20260330T021936Z" / "summary.json",
        help="Path to a processed run summary.json file.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_lexical_index.json",
        help="Path to the chunk lexical index JSON file.",
    )
    parser.add_argument("--condition", help="Filter by normalized condition label.")
    parser.add_argument("--phase", help="Filter by phase, for example PHASE3.")
    parser.add_argument("--study-type", help="Filter by study type, for example INTERVENTIONAL.")
    parser.add_argument(
        "--accepted-only",
        action="store_true",
        help="Limit to trials accepted by validation.",
    )
    parser.add_argument(
        "--year-2026-only",
        action="store_true",
        help="Limit to trials marked as 2026 relevant.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of chunk hits to return.",
    )
    return parser.parse_args()


def trial_matches_filters(
    study_item: dict[str, Any],
    *,
    condition: str | None,
    phase: str | None,
    study_type: str | None,
    accepted_only: bool,
    year_2026_only: bool,
) -> bool:
    validation = study_item.get("validation", {})
    summary = validation.get("summary", {})

    if accepted_only and not validation.get("accepted"):
        return False
    if year_2026_only and not summary.get("is_2026_relevant"):
        return False
    if condition:
        labels = summary.get("condition_labels", [])
        if not isinstance(labels, list) or condition not in labels:
            return False
    if phase:
        phases = summary.get("phases", [])
        if not isinstance(phases, list) or phase not in phases:
            return False
    if study_type and summary.get("study_type") != study_type:
        return False
    return True


def eligible_trial_ids(summary_payload: dict[str, Any], args: argparse.Namespace) -> set[str]:
    allowed: set[str] = set()
    for study_item in summary_payload.get("studies", []):
        if not isinstance(study_item, dict):
            continue
        if trial_matches_filters(
            study_item,
            condition=args.condition,
            phase=args.phase,
            study_type=args.study_type,
            accepted_only=args.accepted_only,
            year_2026_only=args.year_2026_only,
        ):
            nct_id = study_item.get("nct_id")
            if isinstance(nct_id, str):
                allowed.add(nct_id)
    return allowed


def hybrid_search(index: dict[str, Any], allowed_trial_ids: set[str], query: str, limit: int) -> list[dict[str, Any]]:
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
    summary_payload = load_index_json(args.summary_path)
    index = load_index_json(args.index_path)
    allowed_trial_ids = eligible_trial_ids(summary_payload, args)
    results = hybrid_search(index, allowed_trial_ids, args.query, args.limit)
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
                "eligible_trial_count": len(allowed_trial_ids),
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
