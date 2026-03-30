#!/usr/bin/env python3
"""Load one processed trial run into Postgres + pgvector."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from lib.env_utils import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a processed run into the Postgres trial corpus schema."
    )
    parser.add_argument(
        "summary_path",
        type=Path,
        help="Path to processed run summary.json.",
    )
    parser.add_argument(
        "--semantic-index-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_semantic_index.json",
        help="Optional semantic index path used to attach chunk embeddings.",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip loading embeddings even if a semantic index is available.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(float(value)) for value in values) + "]"


def get_db_connection():
    load_dotenv(Path.cwd())
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required to load data into Postgres. Install it in your venv first."
        ) from exc

    import os

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set in the environment or .env file.")
    return psycopg.connect(database_url)


def upsert_trial(cur, normalized_payload: dict[str, Any], raw_payload: dict[str, Any]) -> str:
    trial = normalized_payload["trial"]
    cur.execute(
        """
        INSERT INTO trials (
            nct_id, source, source_url, brief_title, official_title, brief_summary,
            detailed_description, study_type, phases, allocation, intervention_model,
            masking, primary_purpose, enrollment_count, enrollment_type, overall_status,
            last_known_status, start_date_text, primary_completion_date_text,
            completion_date_text, study_first_posted_at_text, results_first_posted_at_text,
            last_update_posted_at_text, is_2026_relevant, relevance_reasons,
            lead_sponsor_name, lead_sponsor_class, collaborator_names, sex,
            minimum_age_text, maximum_age_text, age_groups, healthy_volunteers,
            condition_labels, intervention_labels, drug_class_labels, keyword_labels,
            country_codes, has_us_sites, raw_has_results, raw_payload, updated_at
        ) VALUES (
            %(nct_id)s, %(source)s, %(source_url)s, %(brief_title)s, %(official_title)s, %(brief_summary)s,
            %(detailed_description)s, %(study_type)s, %(phases)s, %(allocation)s, %(intervention_model)s,
            %(masking)s, %(primary_purpose)s, %(enrollment_count)s, %(enrollment_type)s, %(overall_status)s,
            %(last_known_status)s, %(start_date)s, %(primary_completion_date)s,
            %(completion_date)s, %(study_first_posted_at)s, %(results_first_posted_at)s,
            %(last_update_posted_at)s, %(is_2026_relevant)s, %(relevance_reasons)s,
            %(lead_sponsor_name)s, %(lead_sponsor_class)s, %(collaborator_names)s, %(sex)s,
            %(minimum_age_text)s, %(maximum_age_text)s, %(age_groups)s, %(healthy_volunteers)s,
            %(condition_labels)s, %(intervention_labels)s, %(drug_class_labels)s, %(keyword_labels)s,
            %(country_codes)s, %(has_us_sites)s, %(raw_has_results)s, %(raw_payload)s, NOW()
        )
        ON CONFLICT (nct_id) DO UPDATE SET
            source = EXCLUDED.source,
            source_url = EXCLUDED.source_url,
            brief_title = EXCLUDED.brief_title,
            official_title = EXCLUDED.official_title,
            brief_summary = EXCLUDED.brief_summary,
            detailed_description = EXCLUDED.detailed_description,
            study_type = EXCLUDED.study_type,
            phases = EXCLUDED.phases,
            allocation = EXCLUDED.allocation,
            intervention_model = EXCLUDED.intervention_model,
            masking = EXCLUDED.masking,
            primary_purpose = EXCLUDED.primary_purpose,
            enrollment_count = EXCLUDED.enrollment_count,
            enrollment_type = EXCLUDED.enrollment_type,
            overall_status = EXCLUDED.overall_status,
            last_known_status = EXCLUDED.last_known_status,
            start_date_text = EXCLUDED.start_date_text,
            primary_completion_date_text = EXCLUDED.primary_completion_date_text,
            completion_date_text = EXCLUDED.completion_date_text,
            study_first_posted_at_text = EXCLUDED.study_first_posted_at_text,
            results_first_posted_at_text = EXCLUDED.results_first_posted_at_text,
            last_update_posted_at_text = EXCLUDED.last_update_posted_at_text,
            is_2026_relevant = EXCLUDED.is_2026_relevant,
            relevance_reasons = EXCLUDED.relevance_reasons,
            lead_sponsor_name = EXCLUDED.lead_sponsor_name,
            lead_sponsor_class = EXCLUDED.lead_sponsor_class,
            collaborator_names = EXCLUDED.collaborator_names,
            sex = EXCLUDED.sex,
            minimum_age_text = EXCLUDED.minimum_age_text,
            maximum_age_text = EXCLUDED.maximum_age_text,
            age_groups = EXCLUDED.age_groups,
            healthy_volunteers = EXCLUDED.healthy_volunteers,
            condition_labels = EXCLUDED.condition_labels,
            intervention_labels = EXCLUDED.intervention_labels,
            drug_class_labels = EXCLUDED.drug_class_labels,
            keyword_labels = EXCLUDED.keyword_labels,
            country_codes = EXCLUDED.country_codes,
            has_us_sites = EXCLUDED.has_us_sites,
            raw_has_results = EXCLUDED.raw_has_results,
            raw_payload = EXCLUDED.raw_payload,
            updated_at = NOW()
        RETURNING id
        """,
        {**trial, "raw_payload": json.dumps(raw_payload)},
    )
    return str(cur.fetchone()[0])


def refresh_child_tables(cur, trial_id: str, normalized_payload: dict[str, Any], validation_payload: dict[str, Any], chunk_payload: dict[str, Any], embedding_map: dict[str, list[float]]) -> None:
    for table in [
        "trial_conditions",
        "trial_interventions",
        "trial_arms",
        "trial_outcomes",
        "trial_locations",
        "trial_chunks",
    ]:
        cur.execute(f"DELETE FROM {table} WHERE trial_id = %s", (trial_id,))
    cur.execute("DELETE FROM trial_eligibility WHERE trial_id = %s", (trial_id,))
    cur.execute("DELETE FROM trial_validation WHERE trial_id = %s", (trial_id,))

    for row in normalized_payload.get("conditions", []):
        cur.execute(
            """
            INSERT INTO trial_conditions (trial_id, name, normalized_name, is_primary)
            VALUES (%s, %s, %s, %s)
            """,
            (trial_id, row.get("name"), row.get("normalized_name"), row.get("is_primary", True)),
        )

    for row in normalized_payload.get("interventions", []):
        cur.execute(
            """
            INSERT INTO trial_interventions (
                trial_id, intervention_type, name, normalized_name, description,
                arm_group_labels, drug_class
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                trial_id,
                row.get("intervention_type"),
                row.get("name"),
                row.get("normalized_name"),
                row.get("description"),
                row.get("arm_group_labels", []),
                row.get("drug_class"),
            ),
        )

    for row in normalized_payload.get("arms", []):
        cur.execute(
            """
            INSERT INTO trial_arms (trial_id, label, type, description, intervention_names)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (trial_id, row.get("label"), row.get("type"), row.get("description"), row.get("intervention_names", [])),
        )

    for row in normalized_payload.get("outcomes", []):
        cur.execute(
            """
            INSERT INTO trial_outcomes (trial_id, outcome_type, measure, description, time_frame)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                trial_id,
                row.get("outcome_type"),
                row.get("measure"),
                row.get("description"),
                row.get("time_frame"),
            ),
        )

    for row in normalized_payload.get("locations", []):
        cur.execute(
            """
            INSERT INTO trial_locations (trial_id, facility_name, city, state, country, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                trial_id,
                row.get("facility_name"),
                row.get("city"),
                row.get("state"),
                row.get("country"),
                row.get("status"),
            ),
        )

    eligibility = normalized_payload.get("eligibility", {})
    cur.execute(
        """
        INSERT INTO trial_eligibility (
            trial_id, criteria_text, sex, minimum_age_text, maximum_age_text, age_groups, healthy_volunteers
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            trial_id,
            eligibility.get("criteria_text"),
            eligibility.get("sex"),
            eligibility.get("minimum_age_text"),
            eligibility.get("maximum_age_text"),
            eligibility.get("age_groups", []),
            eligibility.get("healthy_volunteers"),
        ),
    )

    cur.execute(
        """
        INSERT INTO trial_validation (
            trial_id, accepted, errors, rejection_reasons, warning_reasons
        ) VALUES (%s, %s, %s, %s, %s)
        """,
        (
            trial_id,
            validation_payload.get("accepted"),
            validation_payload.get("errors", []),
            validation_payload.get("rejection_reasons", []),
            validation_payload.get("warning_reasons", []),
        ),
    )

    for row in chunk_payload.get("chunks", []):
        embedding = embedding_map.get(row["chunk_id"])
        if embedding and len(embedding) == 1536:
            cur.execute(
                """
                INSERT INTO trial_chunks (
                    chunk_id, trial_id, trial_nct_id, chunk_type, title, content,
                    source_field_paths, token_count_estimate, content_tsv, embedding
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, to_tsvector('english', %s), %s::vector
                )
                """,
                (
                    row.get("chunk_id"),
                    trial_id,
                    row.get("trial_nct_id"),
                    row.get("chunk_type"),
                    row.get("title"),
                    row.get("content"),
                    row.get("source_field_paths", []),
                    row.get("token_count_estimate"),
                    row.get("content"),
                    vector_literal(embedding),
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO trial_chunks (
                    chunk_id, trial_id, trial_nct_id, chunk_type, title, content,
                    source_field_paths, token_count_estimate, content_tsv
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, to_tsvector('english', %s)
                )
                """,
                (
                    row.get("chunk_id"),
                    trial_id,
                    row.get("trial_nct_id"),
                    row.get("chunk_type"),
                    row.get("title"),
                    row.get("content"),
                    row.get("source_field_paths", []),
                    row.get("token_count_estimate"),
                    row.get("content"),
                ),
            )


def load_embedding_map(index_path: Path | None, skip_embeddings: bool) -> dict[str, list[float]]:
    if skip_embeddings or index_path is None or not index_path.exists():
        return {}
    payload = load_json(index_path)
    embeddings = payload.get("embeddings", {})
    result: dict[str, list[float]] = {}
    for chunk_id, vector in embeddings.items():
        if isinstance(chunk_id, str) and isinstance(vector, list):
            result[chunk_id] = [float(value) for value in vector]
    return result


def main() -> int:
    args = parse_args()
    summary_payload = load_json(args.summary_path)
    embedding_map = load_embedding_map(args.semantic_index_path, args.skip_embeddings)

    try:
        conn = get_db_connection()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    loaded_count = 0
    with conn:
        with conn.cursor() as cur:
            for study_item in summary_payload.get("studies", []):
                raw_payload = load_json(Path(study_item["raw_path"]))
                normalized_payload = load_json(Path(study_item["normalized_path"]))
                validation_payload = load_json(Path(study_item["validation_path"]))
                chunk_payload = load_json(Path(study_item["chunk_path"]))

                trial_id = upsert_trial(cur, normalized_payload, raw_payload)
                refresh_child_tables(cur, trial_id, normalized_payload, validation_payload, chunk_payload, embedding_map)
                loaded_count += 1

    print(f"Loaded {loaded_count} trials into Postgres")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
