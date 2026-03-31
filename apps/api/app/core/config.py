from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from scripts.lib.env_utils import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    ingestion_queue_name: str


def get_settings() -> Settings:
    load_dotenv(Path.cwd())
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set in the environment or .env file.")
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    ingestion_queue_name = os.environ.get("INGESTION_QUEUE_NAME", "trial_ingestion")
    return Settings(
        database_url=database_url,
        redis_url=redis_url,
        ingestion_queue_name=ingestion_queue_name,
    )
