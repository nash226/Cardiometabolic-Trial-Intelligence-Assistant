from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .schemas.ask import AskRequest, AskResponse
from .schemas.fused_search import FusedSearchRequest, FusedSearchResponse
from .schemas.search import SearchRequest, SearchResponse
from .schemas.semantic_search import SemanticSearchRequest, SemanticSearchResponse
from .services.ask_service import answer_question
from .services.fused_search_service import fused_search_trials
from .services.search_service import search_trials
from .services.semantic_search_service import semantic_search_trials


app = FastAPI(title="Trial Intelligence API", version="0.1.0")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/search", response_model=SearchResponse)
def search_endpoint(request: SearchRequest) -> SearchResponse:
    try:
        return search_trials(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/v1/search/semantic", response_model=SemanticSearchResponse)
def semantic_search_endpoint(request: SemanticSearchRequest) -> SemanticSearchResponse:
    try:
        return semantic_search_trials(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/v1/search/fused", response_model=FusedSearchResponse)
def fused_search_endpoint(request: FusedSearchRequest) -> FusedSearchResponse:
    try:
        return fused_search_trials(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/v1/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest) -> AskResponse:
    try:
        return answer_question(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
