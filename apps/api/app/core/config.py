from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from scripts.lib.env_utils import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str


def get_settings() -> Settings:
    load_dotenv(Path.cwd())
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set in the environment or .env file.")
    return Settings(database_url=database_url)
