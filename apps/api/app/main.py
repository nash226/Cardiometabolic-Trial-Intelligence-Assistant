from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .schemas.ask import AskRequest, AskResponse
from .schemas.ingestion_job import (
    IngestionJobCreateRequest,
    IngestionJobListResponse,
    IngestionJobResponse,
)
from .schemas.fused_search import FusedSearchRequest, FusedSearchResponse
from .schemas.search import SearchRequest, SearchResponse
from .schemas.semantic_search import SemanticSearchRequest, SemanticSearchResponse
from .schemas.trial_detail import TrialDetail
from .services.ask_service import answer_question
from .services.ingestion_job_service import (
    enqueue_ingestion_job,
    get_ingestion_job,
    list_ingestion_jobs,
)
from .services.fused_search_service import fused_search_trials
from .services.search_service import search_trials
from .services.semantic_search_service import semantic_search_trials
from .services.trial_detail_service import get_trial_detail


app = FastAPI(title="Trial Intelligence API", version="0.1.0")
templates = Jinja2Templates(directory="apps/api/app/templates")


@app.get("/", response_class=HTMLResponse)
def finder_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


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


@app.get("/api/v1/trials/{nct_id}", response_model=TrialDetail)
def trial_detail_endpoint(nct_id: str) -> TrialDetail:
    try:
        trial = get_trial_detail(nct_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if trial is None:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")
    return trial


@app.post("/api/v1/ingestion/jobs", response_model=IngestionJobResponse)
def create_ingestion_job(request: IngestionJobCreateRequest) -> IngestionJobResponse:
    try:
        return enqueue_ingestion_job(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/ingestion/jobs", response_model=IngestionJobListResponse)
def list_ingestion_jobs_endpoint() -> IngestionJobListResponse:
    try:
        return IngestionJobListResponse(jobs=list_ingestion_jobs())
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/v1/ingestion/jobs/{job_id}", response_model=IngestionJobResponse)
def get_ingestion_job_endpoint(job_id: str) -> IngestionJobResponse:
    try:
        return get_ingestion_job(job_id)
    except RuntimeError as exc:
        if "not found" in str(exc):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/trials/{nct_id}", response_class=HTMLResponse)
def trial_detail_page(request: Request, nct_id: str):
    try:
        trial = get_trial_detail(nct_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if trial is None:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")
    return templates.TemplateResponse(
        request=request,
        name="trial_detail.html",
        context={"trial": trial},
    )
