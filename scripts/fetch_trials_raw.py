#!/usr/bin/env python3
"""Fetch raw ClinicalTrials.gov study records and save them unchanged.

This is the first executable ingestion step for the project.
It intentionally does not normalize, filter deeply, or chunk the records.
Its only job is to:

1. query the ClinicalTrials.gov API v2
2. download a small batch of study records
3. save the raw JSON for later inspection
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
DEFAULT_OUTPUT_DIR = Path("data/raw")


@dataclass
class FetchConfig:
    query_term: str | None
    query_cond: str | None
    query_intr: str | None
    query_locn: str | None
    filter_overall_status: list[str]
    filter_phase: list[str]
    filter_advanced: str | None
    page_size: int
    max_studies: int
    include_total_count: bool
    delay_seconds: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch raw study records from ClinicalTrials.gov API v2."
    )
    parser.add_argument(
        "--query-term",
        help="General text query, used for broad matching across indexed fields.",
    )
    parser.add_argument(
        "--query-cond",
        help="Condition query, such as 'obesity' or 'type 2 diabetes'.",
    )
    parser.add_argument(
        "--query-intr",
        help="Intervention query, such as 'tirzepatide'.",
    )
    parser.add_argument(
        "--query-locn",
        help="Location query, such as 'United States'.",
    )
    parser.add_argument(
        "--filter-overall-status",
        action="append",
        default=[],
        help=(
            "Repeatable overall status filter, for example RECRUITING or "
            "ACTIVE_NOT_RECRUITING."
        ),
    )
    parser.add_argument(
        "--filter-phase",
        action="append",
        default=[],
        help=(
            "Repeatable phase filter, for example PHASE2, PHASE3, or PHASE4. "
            "This is translated into filter.advanced because the v2 API does not "
            "expose a direct filter.phase parameter."
        ),
    )
    parser.add_argument(
        "--filter-advanced",
        help=(
            "Raw ClinicalTrials.gov advanced filter expression, for example "
            "'AREA[Phase]PHASE3 AND AREA[StudyType]INTERVENTIONAL'."
        ),
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=10,
        help="How many studies to request per API page. Keep this small while learning.",
    )
    parser.add_argument(
        "--max-studies",
        type=int,
        default=10,
        help="Maximum number of studies to save in this run.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Root directory where raw study records will be written.",
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=0.25,
        help="Delay between paginated requests to avoid hammering the public API.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the first request URL and exit without making a network call.",
    )
    args = parser.parse_args()

    if not any([args.query_term, args.query_cond, args.query_intr]):
        parser.error("At least one of --query-term, --query-cond, or --query-intr is required.")

    if args.page_size < 1 or args.page_size > 1000:
        parser.error("--page-size must be between 1 and 1000.")

    if args.max_studies < 1:
        parser.error("--max-studies must be at least 1.")

    return args


def build_config(args: argparse.Namespace) -> FetchConfig:
    return FetchConfig(
        query_term=args.query_term,
        query_cond=args.query_cond,
        query_intr=args.query_intr,
        query_locn=args.query_locn,
        filter_overall_status=args.filter_overall_status,
        filter_phase=args.filter_phase,
        filter_advanced=args.filter_advanced,
        page_size=args.page_size,
        max_studies=args.max_studies,
        include_total_count=True,
        delay_seconds=args.delay_seconds,
    )


def make_request_url(base_url: str, params: dict[str, Any]) -> str:
    query_string = urlencode(params, doseq=True)
    return f"{base_url}?{query_string}"


def build_request_params(config: FetchConfig, page_token: str | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {
        "format": "json",
        "countTotal": str(config.include_total_count).lower(),
        "pageSize": config.page_size,
    }
    if config.query_term:
        params["query.term"] = config.query_term
    if config.query_cond:
        params["query.cond"] = config.query_cond
    if config.query_intr:
        params["query.intr"] = config.query_intr
    if config.query_locn:
        params["query.locn"] = config.query_locn
    advanced_clauses: list[str] = []
    if config.filter_advanced:
        advanced_clauses.append(config.filter_advanced)
    if config.filter_overall_status:
        status_clause = " OR ".join(
            f"AREA[OverallStatus]{status}" for status in config.filter_overall_status
        )
        if len(config.filter_overall_status) > 1:
            status_clause = f"({status_clause})"
        advanced_clauses.append(status_clause)
    if config.filter_phase:
        phase_clause = " OR ".join(f"AREA[Phase]{phase}" for phase in config.filter_phase)
        if len(config.filter_phase) > 1:
            phase_clause = f"({phase_clause})"
        advanced_clauses.append(phase_clause)
    if advanced_clauses:
        params["filter.advanced"] = " AND ".join(advanced_clauses)
    if page_token:
        params["pageToken"] = page_token
    return params


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "cardiometabolic-trial-intelligence-assistant/0.1",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error {exc.code} for URL: {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error for URL: {url}: {exc.reason}") from exc


def ensure_run_directories(output_root: Path) -> tuple[Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = output_root / timestamp
    studies_dir = run_dir / "studies"
    studies_dir.mkdir(parents=True, exist_ok=False)
    return run_dir, studies_dir


def extract_nct_id(study: dict[str, Any], fallback_index: int) -> str:
    identification = study.get("protocolSection", {}).get("identificationModule", {})
    nct_id = identification.get("nctId")
    if nct_id:
        return str(nct_id)
    return f"unknown-study-{fallback_index:04d}"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def collect_studies(config: FetchConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    saved_studies: list[dict[str, Any]] = []
    page_summaries: list[dict[str, Any]] = []
    page_token: str | None = None
    page_number = 0

    while len(saved_studies) < config.max_studies:
        page_number += 1
        params = build_request_params(config, page_token=page_token)
        url = make_request_url(API_BASE_URL, params)
        payload = fetch_json(url)

        studies = payload.get("studies", [])
        next_page_token = payload.get("nextPageToken")
        total_count = payload.get("totalCount")

        page_summaries.append(
            {
                "page_number": page_number,
                "request_url": url,
                "returned_study_count": len(studies),
                "next_page_token": next_page_token,
                "total_count": total_count,
            }
        )

        if not studies:
            break

        remaining = config.max_studies - len(saved_studies)
        saved_studies.extend(studies[:remaining])

        if len(saved_studies) >= config.max_studies or not next_page_token:
            break

        page_token = next_page_token
        time.sleep(config.delay_seconds)

    return saved_studies, page_summaries


def build_manifest(
    config: FetchConfig,
    run_dir: Path,
    studies: list[dict[str, Any]],
    page_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    nct_ids = [extract_nct_id(study, idx + 1) for idx, study in enumerate(studies)]
    return {
        "run_generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base_url": API_BASE_URL,
        "run_directory": str(run_dir),
        "config": asdict(config),
        "study_count": len(studies),
        "nct_ids": nct_ids,
        "pages": page_summaries,
    }


def save_run(output_root: Path, config: FetchConfig) -> Path:
    run_dir, studies_dir = ensure_run_directories(output_root)
    studies, page_summaries = collect_studies(config)

    for index, study in enumerate(studies, start=1):
        nct_id = extract_nct_id(study, index)
        study_path = studies_dir / f"{nct_id}.json"
        write_json(study_path, study)

    manifest = build_manifest(config, run_dir, studies, page_summaries)
    write_json(run_dir / "manifest.json", manifest)

    return run_dir


def main() -> int:
    args = parse_args()
    config = build_config(args)
    first_request_url = make_request_url(API_BASE_URL, build_request_params(config))

    if args.dry_run:
        print(first_request_url)
        return 0

    try:
        run_dir = save_run(args.output_dir, config)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Saved raw study records to {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
