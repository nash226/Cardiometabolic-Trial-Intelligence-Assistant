from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IngestionJobCreateRequest(BaseModel):
    query_term: str | None = None
    query_cond: str | None = None
    query_intr: str | None = None
    query_locn: str | None = None
    filter_overall_status: list[str] = Field(default_factory=list)
    filter_phase: list[str] = Field(default_factory=list)
    filter_advanced: str | None = None
    page_size: int = Field(default=25, ge=1, le=1000)
    max_studies: int = Field(default=100, ge=1, le=5000)
    delay_seconds: float = Field(default=0.25, ge=0.0)
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"


class IngestionJobResponse(BaseModel):
    id: str
    queue_job_id: str | None = None
    status: str
    params: dict[str, object]
    raw_run_directory: str | None = None
    processed_summary_path: str | None = None
    semantic_index_path: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class IngestionJobListResponse(BaseModel):
    jobs: list[IngestionJobResponse]
