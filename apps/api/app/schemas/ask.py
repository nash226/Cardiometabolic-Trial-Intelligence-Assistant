from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    condition: str | None = None
    phase: str | None = None
    study_type: str | None = None
    accepted_only: bool = True
    year_2026_only: bool = True
    retrieval_limit: int = Field(default=5, ge=1, le=20)
    provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    answer_model: str = "gpt-4o-mini"
    lexical_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    semantic_weight: float = Field(default=0.6, ge=0.0, le=1.0)


class AskCitation(BaseModel):
    chunk_id: str
    trial_nct_id: str
    chunk_type: str
    title: str | None = None
    snippet: str
    source_field_paths: list[str]


class AskResponse(BaseModel):
    question: str
    answer: str
    method: str
    warnings: list[str]
    citations: list[AskCitation]
