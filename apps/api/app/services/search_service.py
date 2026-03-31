from __future__ import annotations

from app.db.connection import get_connection
from app.schemas.search import SearchRequest, SearchResponse, SearchResult


def _build_where_clause(request: SearchRequest) -> tuple[str, list[object]]:
    clauses: list[str] = []
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

    if not clauses:
        return "TRUE", params
    return " AND ".join(clauses), params


def search_trials(request: SearchRequest) -> SearchResponse:
    where_sql, where_params = _build_where_clause(request)
    sql = f"""
        WITH eligible_trials AS (
            SELECT t.id, t.nct_id
            FROM trials t
            JOIN trial_validation tv ON tv.trial_id = t.id
            WHERE {where_sql}
        ),
        ranked_chunks AS (
            SELECT
                tc.chunk_id,
                tc.trial_nct_id,
                tc.chunk_type,
                tc.title,
                tc.content,
                tc.source_field_paths,
                ts_rank_cd(tc.content_tsv, websearch_to_tsquery('english', %s)) AS score
            FROM trial_chunks tc
            JOIN eligible_trials et ON et.id = tc.trial_id
            WHERE tc.content_tsv @@ websearch_to_tsquery('english', %s)
        )
        SELECT
            chunk_id,
            trial_nct_id,
            chunk_type,
            title,
            content,
            source_field_paths,
            score
        FROM ranked_chunks
        ORDER BY score DESC, chunk_id ASC
        LIMIT %s
    """
    params = [*where_params, request.query, request.query, request.limit]

    count_sql = f"""
        SELECT COUNT(*)
        FROM trials t
        JOIN trial_validation tv ON tv.trial_id = t.id
        WHERE {where_sql}
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.execute(count_sql, where_params)
            eligible_trial_count = int(cur.fetchone()[0])

    results = [
        SearchResult(
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

    return SearchResponse(
        query=request.query,
        filters={
            "condition": request.condition,
            "phase": request.phase,
            "study_type": request.study_type,
            "accepted_only": request.accepted_only,
            "year_2026_only": request.year_2026_only,
        },
        eligible_trial_count=eligible_trial_count,
        results=results,
    )
