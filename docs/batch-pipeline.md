# Batch Pipeline

The batch pipeline is the first step where we treat the ingestion scripts as one system instead of isolated utilities.

## Script

- [scripts/process_raw_run.py](../scripts/process_raw_run.py)

## What it does

Given one raw fetch run directory:

- reads every study JSON file under `studies/`
- normalizes each study
- validates each normalized record
- generates retrieval chunks for each normalized record
- writes batch outputs into a processed-run folder
- produces a `summary.json` report

## Why this matters

Single-record scripts prove the logic works.

The batch runner answers more important questions:

- how many studies are accepted?
- how many are rejected?
- why are they rejected?
- what warnings are common?

That is the first real view of corpus construction behavior.

## Output layout

For a raw run like:

- `data/raw/20260327T175821Z`

The batch runner writes:

```text
data/processed_runs/20260327T175821Z/
├── chunks/
├── normalized/
├── validation/
└── summary.json
```

## Example usage

```bash
python3 scripts/process_raw_run.py data/raw/20260327T175821Z
```

## Summary contents

The summary includes:

- total study count
- accepted count
- rejected count
- accepted `nct_id` values
- rejected `nct_id` values
- rejection reason counts
- warning reason counts
- per-study output paths and validation results

## Why the batch runner imports logic directly

The script imports the existing `normalize_trial` and `validate_trial` functions instead of shelling out to the CLI scripts.

Reason:

- less duplication
- easier testing
- clearer control flow
- easier to extend later into a larger ETL pipeline
