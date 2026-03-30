#!/usr/bin/env python3
"""Apply SQL migrations for the trial corpus schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.env_utils import load_dotenv


DEFAULT_MIGRATIONS_DIR = Path("apps") / "api" / "db" / "migrations"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run SQL migrations against the configured Postgres database."
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=DEFAULT_MIGRATIONS_DIR,
        help="Directory containing ordered SQL migration files.",
    )
    return parser.parse_args()


def get_db_connection():
    load_dotenv(Path.cwd())
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required to run migrations. Install it in your venv first."
        ) from exc

    import os

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set in the environment or .env file.")
    return psycopg.connect(database_url)


def migration_files(migrations_dir: Path) -> list[Path]:
    if not migrations_dir.exists():
        raise RuntimeError(f"Migrations directory does not exist: {migrations_dir}")
    return sorted(path for path in migrations_dir.glob("*.sql") if path.is_file())


def main() -> int:
    args = parse_args()

    try:
        files = migration_files(args.migrations_dir)
        conn = get_db_connection()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not files:
        print("No migration files found.")
        return 0

    with conn:
        with conn.cursor() as cur:
            for path in files:
                sql = path.read_text(encoding="utf-8")
                cur.execute(sql)
                print(f"Applied migration: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
