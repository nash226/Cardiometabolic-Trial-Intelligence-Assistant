#!/usr/bin/env python3
"""Run semantic search directly from Postgres using pgvector."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib.embedding_utils import embed_text
from lib.env_utils import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search trial chunks from Postgres using pgvector similarity."
    )
    parser.add_argument("query", help="Semantic query text.")
    parser.add_argument("--condition", help="Filter by normalized condition label.")
    parser.add_argument("--phase", help="Filter by phase, for example PHASE3.")
    parser.add_argument("--study-type", help="Filter by study type, for example INTERVENTIONAL.")
    parser.add_argument("--accepted-only", action="store_true", help="Limit to accepted trials.")
    parser.add_argument("--year-2026-only", action="store_true", help="Limit to 2026-relevant trials.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of hits to return.")
    parser.add_argument(
        "--provider",
        choices=["local_debug", "openai"],
        default="openai",
        help="Embedding provider for the query embedding.",
    )
    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
        help="Embedding model for provider=openai.",
    )
    return parser.parse_args()


def get_db_connection():
    load_dotenv(Path.cwd())
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for DB-backed retrieval. Install it in your venv first."
        ) from exc

    import os

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set in the environment or .env file.")
    return psycopg.connect(database_url)


def build_where_clause(args: argparse.Namespace) -> tuple[str, list[object]]:
    clauses: list[str] = ["tc.embedding IS NOT NULL"]
    params: list[object] = []

    if args.accepted_only:
        clauses.append("tv.accepted = TRUE")
    if args.year_2026_only:
        clauses.append("t.is_2026_relevant = TRUE")
    if args.condition:
        clauses.append("%s = ANY(t.condition_labels)")
        params.append(args.condition)
    if args.phase:
        clauses.append("%s = ANY(t.phases)")
        params.append(args.phase)
    if args.study_type:
        clauses.append("t.study_type = %s")
        params.append(args.study_type)

    return " AND ".join(clauses), params


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def main() -> int:
    args = parse_args()

    try:
        conn = get_db_connection()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    query_embedding = embed_text(args.query, provider=args.provider, model=args.model)
    query_vector = vector_literal(query_embedding)
    where_sql, where_params = build_where_clause(args)

    sql = f"""
        WITH eligible_chunks AS (
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
            WHERE {where_sql}
        )
        SELECT
            chunk_id,
            trial_nct_id,
            chunk_type,
            title,
            content,
            source_field_paths,
            score
        FROM eligible_chunks
        ORDER BY score DESC, chunk_id ASC
        LIMIT %s
    """

    params = [query_vector, *where_params, args.limit]

    with conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM trial_chunks tc
                JOIN trials t ON t.id = tc.trial_id
                JOIN trial_validation tv ON tv.trial_id = t.id
                WHERE {where_sql}
                """,
                where_params,
            )
            eligible_chunk_count = int(cur.fetchone()[0])

    results = []
    for row in rows:
        chunk_id, trial_nct_id, chunk_type, title, content, source_field_paths, score = row
        snippet = content[:180].replace("\n", " ").strip()
        results.append(
            {
                "score": float(score),
                "chunk_id": chunk_id,
                "trial_nct_id": trial_nct_id,
                "chunk_type": chunk_type,
                "title": title,
                "snippet": snippet,
                "source_field_paths": source_field_paths,
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
                "provider": args.provider,
                "model": args.model,
                "eligible_chunk_count": eligible_chunk_count,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
