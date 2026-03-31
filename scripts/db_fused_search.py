#!/usr/bin/env python3
"""Run fused lexical + semantic retrieval directly from Postgres."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from db_hybrid_search import build_where_clause as build_lexical_where_clause
from db_hybrid_search import get_db_connection
from db_semantic_search import vector_literal
from lib.embedding_utils import embed_text
from lib.env_utils import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run fused lexical + semantic search from Postgres."
    )
    parser.add_argument("query", help="Search query text.")
    parser.add_argument("--condition", help="Filter by normalized condition label.")
    parser.add_argument("--phase", help="Filter by phase, for example PHASE3.")
    parser.add_argument("--study-type", help="Filter by study type, for example INTERVENTIONAL.")
    parser.add_argument("--accepted-only", action="store_true", help="Limit to accepted trials.")
    parser.add_argument("--year-2026-only", action="store_true", help="Limit to 2026-relevant trials.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of hits to return.")
    parser.add_argument("--lexical-weight", type=float, default=0.5, help="Weight for lexical score.")
    parser.add_argument("--semantic-weight", type=float, default=0.5, help="Weight for semantic score.")
    parser.add_argument("--provider", choices=["local_debug", "openai"], default="openai", help="Embedding provider.")
    parser.add_argument("--model", default="text-embedding-3-small", help="Embedding model for provider=openai.")
    return parser.parse_args()


def normalize_score_map(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    values = list(scores.values())
    low = min(values)
    high = max(values)
    if low == high:
        return {key: 1.0 for key in scores}
    return {key: (value - low) / (high - low) for key, value in scores.items()}


def query_aware_chunk_type_weights(query: str) -> dict[str, float]:
    normalized = query.lower()
    weights = {
        "status_identity": 1.0,
        "conditions_interventions": 1.0,
        "summary_description": 1.0,
        "eligibility": 1.0,
        "outcomes": 1.0,
        "timeline": 1.0,
        "sponsor_locations": 1.0,
    }

    if any(term in normalized for term in ["therapy", "drug", "agonist", "glp", "incretin", "intervention", "treatment"]):
        weights.update(
            {
                "conditions_interventions": 1.25,
                "summary_description": 1.1,
                "outcomes": 1.05,
                "eligibility": 0.8,
                "status_identity": 0.9,
            }
        )

    if any(term in normalized for term in ["eligibility", "include", "inclusion", "exclude", "exclusion", "criteria"]):
        weights.update(
            {
                "eligibility": 1.3,
                "conditions_interventions": 1.0,
                "summary_description": 0.95,
            }
        )

    if any(term in normalized for term in ["date", "timeline", "completion", "recruiting", "status", "posted", "updated"]):
        weights.update(
            {
                "timeline": 1.25,
                "status_identity": 1.1,
                "eligibility": 0.85,
            }
        )

    if any(term in normalized for term in ["endpoint", "outcome", "measure"]):
        weights.update(
            {
                "outcomes": 1.25,
                "summary_description": 1.05,
                "eligibility": 0.85,
            }
        )

    return weights


def main() -> int:
    args = parse_args()

    try:
        conn = get_db_connection()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    load_dotenv(Path.cwd())
    lexical_where_sql, lexical_where_params = build_lexical_where_clause(args)
    semantic_where_sql = "tc.embedding IS NOT NULL"
    semantic_where_params: list[object] = []
    if args.accepted_only:
        semantic_where_sql += " AND tv.accepted = TRUE"
    if args.year_2026_only:
        semantic_where_sql += " AND t.is_2026_relevant = TRUE"
    if args.condition:
        semantic_where_sql += " AND %s = ANY(t.condition_labels)"
        semantic_where_params.append(args.condition)
    if args.phase:
        semantic_where_sql += " AND %s = ANY(t.phases)"
        semantic_where_params.append(args.phase)
    if args.study_type:
        semantic_where_sql += " AND t.study_type = %s"
        semantic_where_params.append(args.study_type)

    query_embedding = embed_text(args.query, provider=args.provider, model=args.model)
    query_vector = vector_literal(query_embedding)

    lexical_sql = f"""
        SELECT
            tc.chunk_id,
            tc.trial_nct_id,
            tc.chunk_type,
            tc.title,
            tc.content,
            tc.source_field_paths,
            ts_rank_cd(tc.content_tsv, websearch_to_tsquery('english', %s)) AS score
        FROM trial_chunks tc
        JOIN trials t ON t.id = tc.trial_id
        JOIN trial_validation tv ON tv.trial_id = t.id
        WHERE {lexical_where_sql}
          AND tc.content_tsv @@ websearch_to_tsquery('english', %s)
    """

    semantic_sql = f"""
        SELECT
            tc.chunk_id,
            tc.trial_nct_id,
            tc.chunk_type,
            tc.title,
            tc.content,
            tc.source_field_paths,
            1 - (tc.embedding <=> %s::vector) AS score
        FROM trial_chunks tc
        JOIN trials t ON t.id = tc.trial_id
        JOIN trial_validation tv ON tv.trial_id = t.id
        WHERE {semantic_where_sql}
    """

    lexical_scores: dict[str, float] = {}
    semantic_scores: dict[str, float] = {}
    chunk_meta: dict[str, dict[str, object]] = {}
    eligible_trial_count = 0

    with conn:
        with conn.cursor() as cur:
            cur.execute(lexical_sql, [*lexical_where_params, args.query, args.query])
            for row in cur.fetchall():
                chunk_id, trial_nct_id, chunk_type, title, content, source_field_paths, score = row
                lexical_scores[chunk_id] = float(score)
                chunk_meta[chunk_id] = {
                    "trial_nct_id": trial_nct_id,
                    "chunk_type": chunk_type,
                    "title": title,
                    "content": content,
                    "source_field_paths": source_field_paths,
                }

            cur.execute(semantic_sql, [query_vector, *semantic_where_params])
            for row in cur.fetchall():
                chunk_id, trial_nct_id, chunk_type, title, content, source_field_paths, score = row
                semantic_scores[chunk_id] = float(score)
                chunk_meta.setdefault(
                    chunk_id,
                    {
                        "trial_nct_id": trial_nct_id,
                        "chunk_type": chunk_type,
                        "title": title,
                        "content": content,
                        "source_field_paths": source_field_paths,
                    },
                )

            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM trials t
                JOIN trial_validation tv ON tv.trial_id = t.id
                WHERE {lexical_where_sql}
                """,
                lexical_where_params,
            )
            eligible_trial_count = int(cur.fetchone()[0])

    norm_lexical = normalize_score_map(lexical_scores)
    norm_semantic = normalize_score_map(semantic_scores)
    chunk_type_weights = query_aware_chunk_type_weights(args.query)
    all_chunk_ids = set(norm_lexical) | set(norm_semantic)
    ranked = []
    for chunk_id in all_chunk_ids:
        chunk_type = str(chunk_meta[chunk_id].get("chunk_type", ""))
        chunk_type_weight = chunk_type_weights.get(chunk_type, 1.0)
        base_score = (args.lexical_weight * norm_lexical.get(chunk_id, 0.0)) + (
            args.semantic_weight * norm_semantic.get(chunk_id, 0.0)
        )
        fused = base_score * chunk_type_weight
        ranked.append((chunk_id, fused))
    ranked.sort(key=lambda item: (-item[1], item[0]))

    results = []
    for chunk_id, fused_score in ranked[: args.limit]:
        meta = chunk_meta[chunk_id]
        content = str(meta.get("content", ""))
        results.append(
            {
                "chunk_id": chunk_id,
                "trial_nct_id": meta.get("trial_nct_id"),
                "chunk_type": meta.get("chunk_type"),
                "title": meta.get("title"),
                "snippet": content[:180].replace("\n", " ").strip(),
                "chunk_type_weight": chunk_type_weights.get(str(meta.get("chunk_type", "")), 1.0),
                "lexical_score_raw": lexical_scores.get(chunk_id, 0.0),
                "semantic_score_raw": semantic_scores.get(chunk_id, 0.0),
                "lexical_score_norm": norm_lexical.get(chunk_id, 0.0),
                "semantic_score_norm": norm_semantic.get(chunk_id, 0.0),
                "fused_score": fused_score,
                "source_field_paths": meta.get("source_field_paths", []),
            }
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
                "provider": args.provider,
                "model": args.model,
                "eligible_trial_count": eligible_trial_count,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
