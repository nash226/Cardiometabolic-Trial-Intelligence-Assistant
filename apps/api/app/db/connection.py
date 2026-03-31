from __future__ import annotations

import psycopg

from ..core.config import get_settings


def get_connection() -> psycopg.Connection:
    settings = get_settings()
    return psycopg.connect(settings.database_url)
