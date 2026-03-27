#!/usr/bin/env python3
"""Normalize one raw ClinicalTrials.gov study record into a simpler internal shape."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MASH_TERMS = ("mash", "nash", "nafld", "masld", "steatohepat")
T2D_TERMS = ("type 2 diabetes", "t2d", "t2dm", "diabetes mellitus type 2")
OBESITY_TERMS = ("obesity", "overweight", "weight loss", "body weight")

DRUG_CLASS_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("dual_gip_glp1_agonist", ("tirzepatide", "survodutide")),
    ("glp1_receptor_agonist", ("semaglutide", "liraglutide", "dulaglutide", "exenatide")),
    ("fgf21_analog", ("efruxifermin", "pegozafermin", "bosnobrogel", "aldafermin")),
    ("thyroid_hormone_receptor_beta_agonist", ("resmetirom",)),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize one raw ClinicalTrials.gov study JSON file."
    )
    parser.add_argument("input_path", type=Path, help="Path to a raw study JSON file.")
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Optional output path. Defaults to data/normalized/<NCT_ID>.json.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get_nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def unique_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def extract_date(module: dict[str, Any], key: str) -> str | None:
    date_struct = module.get(key, {})
    if not isinstance(date_struct, dict):
        return None
    value = date_struct.get("date")
    return value if isinstance(value, str) else None


def classify_condition(label: str) -> str | None:
    normalized = normalize_text(label)
    if any(term in normalized for term in OBESITY_TERMS):
        return "obesity"
    if any(term in normalized for term in T2D_TERMS):
        return "type_2_diabetes"
    if any(term in normalized for term in MASH_TERMS):
        return "mash"
    return None


def classify_drug(name: str) -> str | None:
    normalized = normalize_text(name)
    for drug_class, terms in DRUG_CLASS_RULES:
        if any(term in normalized for term in terms):
            return drug_class
    return None


def build_source_url(nct_id: str | None) -> str | None:
    if not nct_id:
        return None
    return f"https://clinicaltrials.gov/study/{nct_id}"


def derive_2026_relevance(status: str | None, primary_completion: str | None, completion: str | None, results_posted: str | None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if status in {"RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"}:
        reasons.append("active_or_recruiting_status")
    if primary_completion and primary_completion.startswith("2026"):
        reasons.append("primary_completion_in_2026")
    if completion and completion.startswith("2026"):
        reasons.append("completion_in_2026")
    if results_posted and results_posted.startswith("2026"):
        reasons.append("results_posted_in_2026")
    return bool(reasons), reasons


def normalize_trial(raw_study: dict[str, Any]) -> dict[str, Any]:
    protocol = raw_study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    description = protocol.get("descriptionModule", {})
    conditions = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    design_info = design.get("designInfo", {})
    enrollment = design.get("enrollmentInfo", {})
    arms_interventions = protocol.get("armsInterventionsModule", {})
    outcomes = protocol.get("outcomesModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    contacts_locations = protocol.get("contactsLocationsModule", {})
    sponsor_collaborators = protocol.get("sponsorCollaboratorsModule", {})
    lead_sponsor = sponsor_collaborators.get("leadSponsor", {})

    raw_conditions = conditions.get("conditions", []) or []
    raw_keywords = conditions.get("keywords", []) or []
    raw_interventions = arms_interventions.get("interventions", []) or []
    raw_arms = arms_interventions.get("armGroups", []) or []
    raw_locations = contacts_locations.get("locations", []) or []
    raw_primary_outcomes = outcomes.get("primaryOutcomes", []) or []
    raw_secondary_outcomes = outcomes.get("secondaryOutcomes", []) or []
    raw_other_outcomes = outcomes.get("otherOutcomes", []) or []
    raw_collaborators = sponsor_collaborators.get("collaborators", []) or []

    nct_id = identification.get("nctId")
    primary_completion_date = extract_date(status, "primaryCompletionDateStruct")
    completion_date = extract_date(status, "completionDateStruct")
    results_first_posted_at = extract_date(status, "resultsFirstPostDateStruct")
    overall_status = status.get("overallStatus")
    is_2026_relevant, relevance_reasons = derive_2026_relevance(
        overall_status,
        primary_completion_date,
        completion_date,
        results_first_posted_at,
    )

    normalized_conditions = []
    condition_labels: list[str] = []
    for item in raw_conditions:
        if not isinstance(item, str):
            continue
        normalized_name = classify_condition(item)
        normalized_conditions.append(
            {
                "name": item,
                "normalized_name": normalized_name,
                "is_primary": True,
            }
        )
        if normalized_name:
            condition_labels.append(normalized_name)

    normalized_interventions = []
    intervention_labels: list[str] = []
    drug_class_labels: list[str] = []
    for item in raw_interventions:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        drug_class = classify_drug(name)
        intervention_labels.append(name)
        if drug_class:
            drug_class_labels.append(drug_class)
        normalized_interventions.append(
            {
                "intervention_type": item.get("type"),
                "name": name,
                "normalized_name": normalize_text(name),
                "description": item.get("description"),
                "arm_group_labels": item.get("armGroupLabels", []),
                "drug_class": drug_class,
            }
        )

    normalized_arms = []
    for item in raw_arms:
        if not isinstance(item, dict):
            continue
        normalized_arms.append(
            {
                "label": item.get("label"),
                "type": item.get("type"),
                "description": item.get("description"),
                "intervention_names": item.get("interventionNames", []),
            }
        )

    normalized_outcomes = []
    for outcome_type, items in (
        ("primary", raw_primary_outcomes),
        ("secondary", raw_secondary_outcomes),
        ("other", raw_other_outcomes),
    ):
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized_outcomes.append(
                {
                    "outcome_type": outcome_type,
                    "measure": item.get("measure"),
                    "description": item.get("description"),
                    "time_frame": item.get("timeFrame"),
                }
            )

    normalized_locations = []
    country_codes: list[str] = []
    has_us_sites = False
    for item in raw_locations:
        if not isinstance(item, dict):
            continue
        facility = item.get("facility", {}) if isinstance(item.get("facility"), dict) else {}
        geo = facility.get("address", {}) if isinstance(facility.get("address"), dict) else {}
        country = geo.get("country")
        if isinstance(country, str):
            country_codes.append(country)
            if country == "United States":
                has_us_sites = True
        normalized_locations.append(
            {
                "facility_name": facility.get("name"),
                "city": geo.get("city"),
                "state": geo.get("state"),
                "country": country,
                "status": item.get("status"),
            }
        )

    collaborator_names = []
    for item in raw_collaborators:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            collaborator_names.append(item["name"])

    phases = design.get("phases", []) or []
    if isinstance(phases, str):
        phases = [phases]

    trial = {
        "source": "clinicaltrials_gov",
        "source_url": build_source_url(nct_id),
        "raw_has_results": raw_study.get("hasResults"),
        "nct_id": nct_id,
        "brief_title": identification.get("briefTitle"),
        "official_title": identification.get("officialTitle"),
        "brief_summary": description.get("briefSummary"),
        "detailed_description": description.get("detailedDescription"),
        "study_type": design.get("studyType"),
        "phases": phases,
        "allocation": design_info.get("allocation"),
        "intervention_model": design_info.get("interventionModel"),
        "masking": get_nested(design_info, "maskingInfo", "masking"),
        "primary_purpose": design_info.get("primaryPurpose"),
        "enrollment_count": enrollment.get("count"),
        "enrollment_type": enrollment.get("type"),
        "overall_status": overall_status,
        "last_known_status": status.get("lastKnownStatus"),
        "start_date": extract_date(status, "startDateStruct"),
        "primary_completion_date": primary_completion_date,
        "completion_date": completion_date,
        "study_first_posted_at": extract_date(status, "studyFirstPostDateStruct"),
        "results_first_posted_at": results_first_posted_at,
        "last_update_posted_at": extract_date(status, "lastUpdatePostDateStruct"),
        "is_2026_relevant": is_2026_relevant,
        "relevance_reasons": relevance_reasons,
        "lead_sponsor_name": lead_sponsor.get("name"),
        "lead_sponsor_class": lead_sponsor.get("class"),
        "collaborator_names": unique_nonempty(collaborator_names),
        "sex": eligibility.get("sex"),
        "minimum_age_text": eligibility.get("minimumAge"),
        "maximum_age_text": eligibility.get("maximumAge"),
        "age_groups": eligibility.get("stdAges", []),
        "healthy_volunteers": eligibility.get("healthyVolunteers"),
        "criteria_text": eligibility.get("eligibilityCriteria"),
        "condition_labels": unique_nonempty(condition_labels),
        "intervention_labels": unique_nonempty(intervention_labels),
        "drug_class_labels": unique_nonempty(drug_class_labels),
        "keyword_labels": unique_nonempty([item for item in raw_keywords if isinstance(item, str)]),
        "country_codes": unique_nonempty([item for item in country_codes if isinstance(item, str)]),
        "has_us_sites": has_us_sites,
    }

    return {
        "trial": trial,
        "conditions": normalized_conditions,
        "interventions": normalized_interventions,
        "arms": normalized_arms,
        "outcomes": normalized_outcomes,
        "locations": normalized_locations,
        "eligibility": {
            "criteria_text": eligibility.get("eligibilityCriteria"),
            "sex": eligibility.get("sex"),
            "minimum_age_text": eligibility.get("minimumAge"),
            "maximum_age_text": eligibility.get("maximumAge"),
            "age_groups": eligibility.get("stdAges", []),
            "healthy_volunteers": eligibility.get("healthyVolunteers"),
        },
    }


def default_output_path(input_path: Path, normalized_payload: dict[str, Any]) -> Path:
    nct_id = get_nested(normalized_payload, "trial", "nct_id") or input_path.stem
    return Path("data/normalized") / f"{nct_id}.json"


def main() -> int:
    args = parse_args()
    try:
        raw_study = load_json(args.input_path)
    except FileNotFoundError:
        print(f"Input file not found: {args.input_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {args.input_path}: {exc}", file=sys.stderr)
        return 1

    normalized_payload = normalize_trial(raw_study)
    output_path = args.output_path or default_output_path(args.input_path, normalized_payload)
    write_json(output_path, normalized_payload)
    print(f"Saved normalized trial to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
