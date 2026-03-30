#!/usr/bin/env python3
"""Validate one normalized trial record against MVP corpus rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_STUDY_TYPE = "INTERVENTIONAL"
ALLOWED_PHASES = {"PHASE2", "PHASE3", "PHASE4"}
ALLOWED_CONDITION_LABELS = {"obesity", "type_2_diabetes", "mash"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate one normalized trial JSON file."
    )
    parser.add_argument("input_path", type=Path, help="Path to a normalized trial JSON file.")
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional output path. Defaults to data/normalized/validation/<NCT_ID>.json.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get_trial(payload: dict[str, Any]) -> dict[str, Any]:
    trial = payload.get("trial")
    return trial if isinstance(trial, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_trial(payload: dict[str, Any]) -> dict[str, Any]:
    trial = get_trial(payload)
    errors: list[str] = []
    warnings: list[str] = []
    rejection_reasons: list[str] = []

    nct_id = trial.get("nct_id")
    brief_title = trial.get("brief_title")
    study_type = trial.get("study_type")
    overall_status = trial.get("overall_status")
    phases = {item for item in as_list(trial.get("phases")) if isinstance(item, str)}
    condition_labels = {
        item for item in as_list(trial.get("condition_labels")) if isinstance(item, str)
    }

    if not nct_id:
        errors.append("missing_nct_id")
    if not brief_title:
        errors.append("missing_brief_title")
    if not study_type:
        errors.append("missing_study_type")
    if not overall_status:
        errors.append("missing_overall_status")

    if study_type and study_type != ALLOWED_STUDY_TYPE:
        rejection_reasons.append("study_type_not_interventional")

    if not phases:
        rejection_reasons.append("missing_phase")
    elif phases.isdisjoint(ALLOWED_PHASES):
        rejection_reasons.append("phase_out_of_scope")

    if not condition_labels:
        rejection_reasons.append("missing_normalized_condition")
    elif condition_labels.isdisjoint(ALLOWED_CONDITION_LABELS):
        rejection_reasons.append("condition_out_of_scope")

    if not trial.get("official_title"):
        warnings.append("missing_official_title")
    if not trial.get("brief_summary"):
        warnings.append("missing_brief_summary")
    if not trial.get("criteria_text"):
        warnings.append("missing_eligibility_criteria")
    if not as_list(payload.get("locations")):
        warnings.append("missing_locations")
    if not as_list(payload.get("outcomes")):
        warnings.append("missing_outcomes")

    accepted = not errors and not rejection_reasons

    return {
        "accepted": accepted,
        "nct_id": nct_id,
        "errors": errors,
        "rejection_reasons": rejection_reasons,
        "warning_reasons": warnings,
        "summary": {
            "study_type": study_type,
            "phases": sorted(phases),
            "condition_labels": sorted(condition_labels),
            "overall_status": overall_status,
            "is_2026_relevant": trial.get("is_2026_relevant"),
            "has_us_sites": trial.get("has_us_sites"),
        },
    }


def default_output_path(input_path: Path, result: dict[str, Any]) -> Path:
    nct_id = result.get("nct_id") or input_path.stem
    return Path("data") / "normalized" / "validation" / f"{nct_id}.json"


def main() -> int:
    args = parse_args()
    try:
        payload = load_json(args.input_path)
    except FileNotFoundError:
        print(f"Input file not found: {args.input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {args.input_path}: {exc}", file=sys.stderr)
        return 1

    result = validate_trial(payload)
    output_path = args.output_path or default_output_path(args.input_path, result)
    write_json(output_path, result)
    status = "accepted" if result["accepted"] else "rejected"
    print(f"Validation {status}: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
