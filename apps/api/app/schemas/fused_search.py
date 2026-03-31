from __future__ import annotations

from pydantic import BaseModel, Field


class FusedSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    condition: str | None = None
    phase: str | None = None
    study_type: str | None = None
    accepted_only: bool = True
    year_2026_only: bool = True
    limit: int = Field(default=5, ge=1, le=50)
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    lexical_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    semantic_weight: float = Field(default=0.5, ge=0.0, le=1.0)


class FusedSearchResult(BaseModel):
    chunk_id: str
    trial_nct_id: str
    trial_title: str | None = None
    chunk_type: str
    title: str | None = None
    snippet: str
    chunk_type_weight: float
    lexical_score_raw: float
    semantic_score_raw: float
    lexical_score_norm: float
    semantic_score_norm: float
    fused_score: float
    source_field_paths: list[str]


class FusedSearchResponse(BaseModel):
    query: str
    filters: dict[str, object]
    weights: dict[str, float]
    provider: str
    model: str
    eligible_trial_count: int
    results: list[FusedSearchResult]
