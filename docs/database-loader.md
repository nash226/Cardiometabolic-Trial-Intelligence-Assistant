# Database Loader

This step moves the processed corpus from file artifacts into Postgres + pgvector.

## Script

- [scripts/load_processed_run_to_db.py](../scripts/load_processed_run_to_db.py)

## What it does

Given one processed run summary:

- loads raw, normalized, validation, and chunk files
- upserts trial rows
- refreshes child tables
- inserts validation state
- inserts chunk rows
- optionally attaches embeddings from the semantic index

## Environment requirements

The loader expects:

- `DATABASE_URL` in the environment or `.env`
- `psycopg` installed in the active virtual environment

## Example usage

Run schema migrations first:

```bash
python3 scripts/run_db_migrations.py
```

Then load the processed run:

```bash
python3 scripts/load_processed_run_to_db.py \
  data/processed_runs_with_chunks/20260330T021936Z/summary.json
```

Skip embeddings:

```bash
python3 scripts/load_processed_run_to_db.py \
  data/processed_runs_with_chunks/20260330T021936Z/summary.json \
  --skip-embeddings
```

## Important behavior

The loader currently:

- upserts the `trials` row by `nct_id`
- deletes and refreshes child rows for that trial
- stores validation explicitly
- keeps rejected trials in the database

## Common setup error

If you see:

```text
psycopg.errors.UndefinedTable: relation "trials" does not exist
```

it means the SQL migrations have not been applied yet.

Run:

```bash
python3 scripts/run_db_migrations.py
```

before running the loader.

## Why this design is acceptable now

For the current MVP stage, the loader favors:

- clarity
- inspectability
- deterministic refresh behavior

over:

- bulk loading optimizations
- advanced incremental sync logic

That is the right tradeoff until the storage layer itself is proven.
