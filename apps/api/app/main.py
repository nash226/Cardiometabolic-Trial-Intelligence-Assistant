from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .schemas.search import SearchRequest, SearchResponse
from .schemas.semantic_search import SemanticSearchRequest, SemanticSearchResponse
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
