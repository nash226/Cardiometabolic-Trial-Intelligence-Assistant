"""Condition taxonomy helpers for cardiometabolic trial normalization."""

from __future__ import annotations

import json
import re
from pathlib import Path


TAXONOMY_PATH = Path(__file__).resolve().parent / "condition_taxonomy.json"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def load_taxonomy() -> dict[str, object]:
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))


def classify_condition(label: str) -> str | None:
    taxonomy = load_taxonomy()
    normalized_label = normalize_text(label)

    explicit_mappings = taxonomy.get("explicit_mappings", {})
    if isinstance(explicit_mappings, dict):
        for raw_label, mapped_label in explicit_mappings.items():
            if normalize_text(raw_label) == normalized_label:
                return mapped_label if isinstance(mapped_label, str) else None

    contains_rules = taxonomy.get("contains_rules", {})
    if isinstance(contains_rules, dict):
        for mapped_label, terms in contains_rules.items():
            if not isinstance(mapped_label, str) or not isinstance(terms, list):
                continue
            if any(term in normalized_label for term in terms if isinstance(term, str)):
                return mapped_label

    return None
