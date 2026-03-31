from __future__ import annotations

from ..db.connection import get_connection
from ..schemas.fused_search import (
    FusedSearchRequest,
    FusedSearchResponse,
    FusedSearchResult,
)
from .search_service import _build_where_clause
from scripts.lib.embedding_utils import embed_text


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def _normalize_score_map(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    low = min(scores.values())
    high = max(scores.values())
    if low == high:
        return {key: 1.0 for key in scores}
    return {key: (value - low) / (high - low) for key, value in scores.items()}


def fused_search_trials(request: FusedSearchRequest) -> FusedSearchResponse:
    where_sql, where_params = _build_where_clause(request)
    query_embedding = embed_text(request.query, provider=request.provider, model=request.model)
    query_vector = _vector_literal(query_embedding)

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
        WHERE {where_sql}
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
        WHERE {where_sql}
          AND tc.embedding IS NOT NULL
    """
    count_sql = f"""
        SELECT COUNT(*)
        FROM trials t
        JOIN trial_validation tv ON tv.trial_id = t.id
        WHERE {where_sql}
    """

    lexical_scores: dict[str, float] = {}
    semantic_scores: dict[str, float] = {}
    chunk_meta: dict[str, dict[str, object]] = {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(lexical_sql, [*where_params, request.query, request.query])
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

            cur.execute(semantic_sql, [query_vector, *where_params])
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

            cur.execute(count_sql, where_params)
            eligible_trial_count = int(cur.fetchone()[0])

    norm_lexical = _normalize_score_map(lexical_scores)
    norm_semantic = _normalize_score_map(semantic_scores)
    all_chunk_ids = set(norm_lexical) | set(norm_semantic)
    ranked = []
    for chunk_id in all_chunk_ids:
        fused_score = (
            request.lexical_weight * norm_lexical.get(chunk_id, 0.0)
            + request.semantic_weight * norm_semantic.get(chunk_id, 0.0)
        )
        ranked.append((chunk_id, fused_score))
    ranked.sort(key=lambda item: (-item[1], item[0]))

    results = []
    for chunk_id, fused_score in ranked[: request.limit]:
        meta = chunk_meta[chunk_id]
        content = str(meta.get("content", ""))
        results.append(
            FusedSearchResult(
                chunk_id=chunk_id,
                trial_nct_id=str(meta.get("trial_nct_id", "")),
                chunk_type=str(meta.get("chunk_type", "")),
                title=meta.get("title"),
                snippet=content[:180].replace("\n", " ").strip(),
                lexical_score_raw=lexical_scores.get(chunk_id, 0.0),
                semantic_score_raw=semantic_scores.get(chunk_id, 0.0),
                lexical_score_norm=norm_lexical.get(chunk_id, 0.0),
                semantic_score_norm=norm_semantic.get(chunk_id, 0.0),
                fused_score=fused_score,
                source_field_paths=list(meta.get("source_field_paths", [])),
            )
        )

    return FusedSearchResponse(
        query=request.query,
        filters={
            "condition": request.condition,
            "phase": request.phase,
            "study_type": request.study_type,
            "accepted_only": request.accepted_only,
            "year_2026_only": request.year_2026_only,
        },
        weights={
            "lexical": request.lexical_weight,
            "semantic": request.semantic_weight,
        },
        provider=request.provider,
        model=request.model,
        eligible_trial_count=eligible_trial_count,
        results=results,
    )
