from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    condition: str | None = None
    phase: str | None = None
    study_type: str | None = None
    accepted_only: bool = True
    year_2026_only: bool = True
    limit: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    score: float
    chunk_id: str
    trial_nct_id: str
    chunk_type: str
    title: str | None = None
    snippet: str
    source_field_paths: list[str]


class SearchResponse(BaseModel):
    query: str
    filters: dict[str, object]
    eligible_trial_count: int
    results: list[SearchResult]
