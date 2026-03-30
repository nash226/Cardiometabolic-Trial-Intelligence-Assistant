#!/usr/bin/env python3
"""Normalize and validate every study in one raw fetch run."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from generate_chunks import generate_chunks, write_json as write_chunk_json
from normalize_trial import load_json as load_raw_json
from normalize_trial import normalize_trial, write_json as write_normalized_json
from validate_trial import validate_trial, write_json as write_validation_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process one raw fetch run into normalized and validation outputs."
    )
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to a raw run directory under data/raw/<timestamp>.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data") / "processed_runs",
        help="Directory where batch outputs and summary files will be written.",
    )
    return parser.parse_args()


def collect_study_files(run_dir: Path) -> list[Path]:
    studies_dir = run_dir / "studies"
    return sorted(studies_dir.glob("*.json"))


def build_output_dirs(output_root: Path, run_name: str) -> tuple[Path, Path, Path, Path]:
    run_output_dir = output_root / run_name
    normalized_dir = run_output_dir / "normalized"
    validation_dir = run_output_dir / "validation"
    chunks_dir = run_output_dir / "chunks"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    return run_output_dir, normalized_dir, validation_dir, chunks_dir


def build_summary(
    run_dir: Path,
    study_results: list[dict[str, Any]],
    rejection_counts: Counter[str],
    warning_counts: Counter[str],
) -> dict[str, Any]:
    accepted = [item for item in study_results if item["validation"]["accepted"]]
    rejected = [item for item in study_results if not item["validation"]["accepted"]]
    return {
        "run_directory": str(run_dir),
        "total_studies": len(study_results),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted_nct_ids": [item["nct_id"] for item in accepted],
        "rejected_nct_ids": [item["nct_id"] for item in rejected],
        "rejection_reason_counts": dict(sorted(rejection_counts.items())),
        "warning_reason_counts": dict(sorted(warning_counts.items())),
        "studies": study_results,
    }


def process_run(run_dir: Path, output_root: Path) -> Path:
    study_files = collect_study_files(run_dir)
    run_output_dir, normalized_dir, validation_dir, chunks_dir = build_output_dirs(output_root, run_dir.name)

    study_results: list[dict[str, Any]] = []
    rejection_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()

    for study_file in study_files:
        raw_payload = load_raw_json(study_file)
        normalized_payload = normalize_trial(raw_payload)
        nct_id = normalized_payload.get("trial", {}).get("nct_id") or study_file.stem

        normalized_path = normalized_dir / f"{nct_id}.json"
        write_normalized_json(normalized_path, normalized_payload)

        validation_payload = validate_trial(normalized_payload)
        validation_path = validation_dir / f"{nct_id}.json"
        write_validation_json(validation_path, validation_payload)

        chunk_payload = generate_chunks(normalized_payload)
        chunk_path = chunks_dir / f"{nct_id}.json"
        write_chunk_json(chunk_path, chunk_payload)

        rejection_counts.update(validation_payload.get("rejection_reasons", []))
        warning_counts.update(validation_payload.get("warning_reasons", []))

        study_results.append(
            {
                "nct_id": nct_id,
                "raw_path": str(study_file),
                "normalized_path": str(normalized_path),
                "validation_path": str(validation_path),
                "chunk_path": str(chunk_path),
                "validation": validation_payload,
            }
        )

    summary = build_summary(run_dir, study_results, rejection_counts, warning_counts)
    summary_path = run_output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path


def main() -> int:
    args = parse_args()
    summary_path = process_run(args.run_dir, args.output_root)
    print(f"Processed raw run summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
