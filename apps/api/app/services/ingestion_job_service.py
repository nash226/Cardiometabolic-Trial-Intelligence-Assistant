from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.build_chunk_embeddings import build_semantic_index, write_json as write_semantic_index
from scripts.fetch_trials_raw import FetchConfig, save_run
from scripts.load_processed_run_to_db import load_processed_run
from scripts.process_raw_run import process_run

from ..core.config import get_settings
from ..db.connection import get_connection
from ..schemas.ingestion_job import IngestionJobCreateRequest, IngestionJobResponse


RAW_OUTPUT_ROOT = Path("data") / "raw"
PROCESSED_OUTPUT_ROOT = Path("data") / "processed_runs_with_chunks"
SEMANTIC_INDEX_OUTPUT_ROOT = Path("data") / "indexes"


def _redis_queue():
    from redis import Redis
    from rq import Queue

    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    return Queue(name=settings.ingestion_queue_name, connection=redis)


def _row_to_job_response(row: tuple[Any, ...]) -> IngestionJobResponse:
    (
        job_id,
        queue_job_id,
        status,
        params,
        raw_run_directory,
        processed_summary_path,
        semantic_index_path,
        error_message,
        created_at,
        started_at,
        finished_at,
    ) = row
    return IngestionJobResponse(
        id=str(job_id),
        queue_job_id=queue_job_id,
        status=status,
        params=params or {},
        raw_run_directory=raw_run_directory,
        processed_summary_path=processed_summary_path,
        semantic_index_path=semantic_index_path,
        error_message=error_message,
        created_at=created_at,
        started_at=started_at,
        finished_at=finished_at,
    )


def _insert_job(request: IngestionJobCreateRequest) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_jobs (status, params)
                VALUES (%s, %s::jsonb)
                RETURNING id
                """,
                ("queued", request.model_dump(mode="json")),
            )
            return str(cur.fetchone()[0])


def _update_queue_job_id(job_id: str, queue_job_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingestion_jobs
                SET queue_job_id = %s
                WHERE id = %s::uuid
                """,
                (queue_job_id, job_id),
            )


def enqueue_ingestion_job(request: IngestionJobCreateRequest) -> IngestionJobResponse:
    if not any([request.query_term, request.query_cond, request.query_intr]):
        raise RuntimeError("At least one of query_term, query_cond, or query_intr is required.")

    job_id = _insert_job(request)
    queue = _redis_queue()
    rq_job = queue.enqueue(run_ingestion_job, job_id, request.model_dump(mode="json"))
    _update_queue_job_id(job_id, rq_job.id)
    return get_ingestion_job(job_id)


def list_ingestion_jobs(limit: int = 25) -> list[IngestionJobResponse]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, queue_job_id, status, params, raw_run_directory,
                    processed_summary_path, semantic_index_path, error_message,
                    created_at, started_at, finished_at
                FROM ingestion_jobs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [_row_to_job_response(row) for row in cur.fetchall()]


def get_ingestion_job(job_id: str) -> IngestionJobResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, queue_job_id, status, params, raw_run_directory,
                    processed_summary_path, semantic_index_path, error_message,
                    created_at, started_at, finished_at
                FROM ingestion_jobs
                WHERE id = %s::uuid
                """,
                (job_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Ingestion job {job_id} not found")
    return _row_to_job_response(row)


def _mark_job_running(job_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingestion_jobs
                SET status = 'running', started_at = NOW(), error_message = NULL
                WHERE id = %s::uuid
                """,
                (job_id,),
            )


def _mark_job_completed(job_id: str, raw_run_directory: str, processed_summary_path: str, semantic_index_path: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'completed',
                    raw_run_directory = %s,
                    processed_summary_path = %s,
                    semantic_index_path = %s,
                    finished_at = NOW()
                WHERE id = %s::uuid
                """,
                (raw_run_directory, processed_summary_path, semantic_index_path, job_id),
            )


def _mark_job_failed(job_id: str, error_message: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingestion_jobs
                SET status = 'failed', error_message = %s, finished_at = NOW()
                WHERE id = %s::uuid
                """,
                (error_message, job_id),
            )


def run_ingestion_job(job_id: str, params: dict[str, Any]) -> None:
    _mark_job_running(job_id)
    try:
        fetch_config = FetchConfig(
            query_term=params.get("query_term"),
            query_cond=params.get("query_cond"),
            query_intr=params.get("query_intr"),
            query_locn=params.get("query_locn"),
            filter_overall_status=list(params.get("filter_overall_status", [])),
            filter_phase=list(params.get("filter_phase", [])),
            filter_advanced=params.get("filter_advanced"),
            page_size=int(params.get("page_size", 25)),
            max_studies=int(params.get("max_studies", 100)),
            include_total_count=True,
            delay_seconds=float(params.get("delay_seconds", 0.25)),
        )

        raw_run_dir = save_run(RAW_OUTPUT_ROOT, fetch_config)
        summary_path = process_run(raw_run_dir, PROCESSED_OUTPUT_ROOT)
        chunks_dir = summary_path.parent / "chunks"
        semantic_index_path = SEMANTIC_INDEX_OUTPUT_ROOT / f"{raw_run_dir.name}_chunk_semantic_index.json"
        semantic_index = build_semantic_index(
            chunks_dir,
            provider=str(params.get("embedding_provider", "openai")),
            model=params.get("embedding_model"),
        )
        write_semantic_index(semantic_index_path, semantic_index)
        load_processed_run(summary_path, semantic_index_path, skip_embeddings=False)
        _mark_job_completed(
            job_id,
            str(raw_run_dir),
            str(summary_path),
            str(semantic_index_path),
        )
    except Exception as exc:
        _mark_job_failed(job_id, str(exc))
        raise
