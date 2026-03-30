"""Minimal .env loading helpers for local development."""

from __future__ import annotations

import os
from pathlib import Path


def find_dotenv(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        dotenv_path = candidate / ".env"
        if dotenv_path.exists():
            return dotenv_path
    return None


def load_dotenv(start: Path | None = None, override: bool = False) -> Path | None:
    dotenv_path = find_dotenv(start)
    if dotenv_path is None:
        return None

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value

    return dotenv_path
