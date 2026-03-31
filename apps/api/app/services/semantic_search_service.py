from __future__ import annotations

from ..db.connection import get_connection
from ..schemas.semantic_search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from scripts.lib.embedding_utils import embed_text


def _build_where_clause(request: SemanticSearchRequest) -> tuple[str, list[object]]:
    clauses: list[str] = ["tc.embedding IS NOT NULL"]
    params: list[object] = []

    if request.accepted_only:
        clauses.append("tv.accepted = TRUE")
    if request.year_2026_only:
        clauses.append("t.is_2026_relevant = TRUE")
    if request.condition:
        clauses.append("%s = ANY(t.condition_labels)")
        params.append(request.condition)
    if request.phase:
        clauses.append("%s = ANY(t.phases)")
        params.append(request.phase)
    if request.study_type:
        clauses.append("t.study_type = %s")
        params.append(request.study_type)

    return " AND ".join(clauses), params


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def semantic_search_trials(request: SemanticSearchRequest) -> SemanticSearchResponse:
    query_embedding = embed_text(request.query, provider=request.provider, model=request.model)
    query_vector = _vector_literal(query_embedding)
    where_sql, where_params = _build_where_clause(request)

    sql = f"""
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
        ORDER BY score DESC, tc.chunk_id ASC
        LIMIT %s
    """
    params = [query_vector, *where_params, request.limit]

    count_sql = f"""
        SELECT COUNT(*)
        FROM trial_chunks tc
        JOIN trials t ON t.id = tc.trial_id
        JOIN trial_validation tv ON tv.trial_id = t.id
        WHERE {where_sql}
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.execute(count_sql, where_params)
            eligible_chunk_count = int(cur.fetchone()[0])

    results = [
        SemanticSearchResult(
            score=float(score),
            chunk_id=chunk_id,
            trial_nct_id=trial_nct_id,
            chunk_type=chunk_type,
            title=title,
            snippet=content[:180].replace("\n", " ").strip(),
            source_field_paths=source_field_paths,
        )
        for chunk_id, trial_nct_id, chunk_type, title, content, source_field_paths, score in rows
    ]

    return SemanticSearchResponse(
        query=request.query,
        filters={
            "condition": request.condition,
            "phase": request.phase,
            "study_type": request.study_type,
            "accepted_only": request.accepted_only,
            "year_2026_only": request.year_2026_only,
        },
        provider=request.provider,
        model=request.model,
        eligible_chunk_count=eligible_chunk_count,
        results=results,
    )
