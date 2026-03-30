#!/usr/bin/env python3
"""Generate field-aware retrieval chunks from one normalized trial record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate retrieval chunks from one normalized trial JSON file."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to a normalized trial JSON file.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional output path. Defaults to data/chunks/<NCT_ID>.json.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def format_list(values: list[str]) -> str:
    cleaned = [normalize_whitespace(value) for value in values if isinstance(value, str) and value.strip()]
    return "; ".join(cleaned)


def approximate_token_count(text: str) -> int:
    return max(1, len(text.split()))


def add_chunk(
    chunks: list[dict[str, Any]],
    nct_id: str,
    chunk_type: str,
    title: str,
    content_parts: list[str],
    source_field_paths: list[str],
) -> None:
    content = "\n".join(part for part in content_parts if part.strip()).strip()
    if not content:
        return
    chunk_id = f"{nct_id}:{chunk_type}:{len(chunks) + 1}"
    chunks.append(
        {
            "chunk_id": chunk_id,
            "trial_nct_id": nct_id,
            "chunk_type": chunk_type,
            "title": title,
            "content": content,
            "source_field_paths": source_field_paths,
            "token_count_estimate": approximate_token_count(content),
        }
    )


def generate_chunks(normalized_payload: dict[str, Any]) -> dict[str, Any]:
    trial = normalized_payload.get("trial", {})
    conditions = normalized_payload.get("conditions", [])
    interventions = normalized_payload.get("interventions", [])
    arms = normalized_payload.get("arms", [])
    outcomes = normalized_payload.get("outcomes", [])
    locations = normalized_payload.get("locations", [])
    eligibility = normalized_payload.get("eligibility", {})

    nct_id = trial.get("nct_id")
    if not isinstance(nct_id, str) or not nct_id:
        raise ValueError("Normalized trial payload is missing trial.nct_id")

    chunks: list[dict[str, Any]] = []

    add_chunk(
        chunks,
        nct_id,
        "status_identity",
        "Status and Identity",
        [
            f"NCT ID: {trial.get('nct_id')}",
            f"Brief title: {trial.get('brief_title')}",
            f"Official title: {trial.get('official_title')}",
            f"Study type: {trial.get('study_type')}",
            f"Overall status: {trial.get('overall_status')}",
            f"Phases: {format_list(trial.get('phases', []))}",
        ],
        [
            "trial.nct_id",
            "trial.brief_title",
            "trial.official_title",
            "trial.study_type",
            "trial.overall_status",
            "trial.phases",
        ],
    )

    add_chunk(
        chunks,
        nct_id,
        "conditions_interventions",
        "Conditions and Interventions",
        [
            f"Condition labels: {format_list(trial.get('condition_labels', []))}",
            f"Raw conditions: {format_list([item.get('name', '') for item in conditions if isinstance(item, dict)])}",
            f"Intervention labels: {format_list(trial.get('intervention_labels', []))}",
            f"Drug class labels: {format_list(trial.get('drug_class_labels', []))}",
            f"Arms: {format_list([item.get('label', '') for item in arms if isinstance(item, dict)])}",
            f"Keywords: {format_list(trial.get('keyword_labels', []))}",
        ],
        [
            "trial.condition_labels",
            "conditions[].name",
            "trial.intervention_labels",
            "trial.drug_class_labels",
            "arms[].label",
            "trial.keyword_labels",
        ],
    )

    add_chunk(
        chunks,
        nct_id,
        "summary_description",
        "Summary and Description",
        [
            f"Brief summary: {trial.get('brief_summary')}",
            f"Detailed description: {trial.get('detailed_description')}",
        ],
        [
            "trial.brief_summary",
            "trial.detailed_description",
        ],
    )

    add_chunk(
        chunks,
        nct_id,
        "eligibility",
        "Eligibility",
        [
            f"Sex: {trial.get('sex')}",
            f"Minimum age: {trial.get('minimum_age_text')}",
            f"Maximum age: {trial.get('maximum_age_text')}",
            f"Age groups: {format_list(trial.get('age_groups', []))}",
            f"Healthy volunteers: {trial.get('healthy_volunteers')}",
            f"Criteria: {eligibility.get('criteria_text')}",
        ],
        [
            "trial.sex",
            "trial.minimum_age_text",
            "trial.maximum_age_text",
            "trial.age_groups",
            "trial.healthy_volunteers",
            "eligibility.criteria_text",
        ],
    )

    if outcomes:
        outcome_lines = []
        for item in outcomes:
            if not isinstance(item, dict):
                continue
            line_parts = [
                f"type={item.get('outcome_type')}",
                f"measure={item.get('measure')}",
                f"time_frame={item.get('time_frame')}",
            ]
            description = item.get("description")
            if description:
                line_parts.append(f"description={description}")
            outcome_lines.append(" | ".join(part for part in line_parts if part))
        add_chunk(
            chunks,
            nct_id,
            "outcomes",
            "Outcomes",
            outcome_lines,
            [
                "outcomes[].outcome_type",
                "outcomes[].measure",
                "outcomes[].time_frame",
                "outcomes[].description",
            ],
        )

    add_chunk(
        chunks,
        nct_id,
        "timeline",
        "Timeline",
        [
            f"Start date: {trial.get('start_date')}",
            f"Primary completion date: {trial.get('primary_completion_date')}",
            f"Completion date: {trial.get('completion_date')}",
            f"Study first posted: {trial.get('study_first_posted_at')}",
            f"Results first posted: {trial.get('results_first_posted_at')}",
            f"Last update posted: {trial.get('last_update_posted_at')}",
            f"2026 relevant: {trial.get('is_2026_relevant')}",
            f"Relevance reasons: {format_list(trial.get('relevance_reasons', []))}",
        ],
        [
            "trial.start_date",
            "trial.primary_completion_date",
            "trial.completion_date",
            "trial.study_first_posted_at",
            "trial.results_first_posted_at",
            "trial.last_update_posted_at",
            "trial.is_2026_relevant",
            "trial.relevance_reasons",
        ],
    )

    location_parts = []
    for item in locations[:25]:
        if not isinstance(item, dict):
            continue
        bits = [item.get("facility_name"), item.get("city"), item.get("state"), item.get("country"), item.get("status")]
        location_line = ", ".join(str(bit) for bit in bits if bit)
        if location_line:
            location_parts.append(location_line)

    add_chunk(
        chunks,
        nct_id,
        "sponsor_locations",
        "Sponsor and Locations",
        [
            f"Lead sponsor: {trial.get('lead_sponsor_name')}",
            f"Lead sponsor class: {trial.get('lead_sponsor_class')}",
            f"Collaborators: {format_list(trial.get('collaborator_names', []))}",
            f"Countries: {format_list(trial.get('country_codes', []))}",
            f"Has US sites: {trial.get('has_us_sites')}",
            f"Location sample: {format_list(location_parts)}",
        ],
        [
            "trial.lead_sponsor_name",
            "trial.lead_sponsor_class",
            "trial.collaborator_names",
            "trial.country_codes",
            "trial.has_us_sites",
            "locations[]",
        ],
    )

    return {
        "trial_nct_id": nct_id,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def default_output_path(input_path: Path, chunk_payload: dict[str, Any]) -> Path:
    nct_id = chunk_payload.get("trial_nct_id") or input_path.stem
    return Path("data") / "chunks" / f"{nct_id}.json"


def main() -> int:
    args = parse_args()
    try:
        normalized_payload = load_json(args.input_path)
    except FileNotFoundError:
        print(f"Input file not found: {args.input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {args.input_path}: {exc}", file=sys.stderr)
        return 1

    try:
        chunk_payload = generate_chunks(normalized_payload)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output_path = args.output_path or default_output_path(args.input_path, chunk_payload)
    write_json(output_path, chunk_payload)
    print(f"Saved chunks to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
