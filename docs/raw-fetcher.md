# Raw Fetcher

This is the first executable ingestion step.

The fetcher does one thing:

- download raw ClinicalTrials.gov study records and save them unchanged

It does not:

- normalize fields
- infer condition classes
- derive 2026 relevance
- chunk text
- write to Postgres

That separation is deliberate. We want the first script to be easy to inspect and reason about.

## Script

- [scripts/fetch_trials_raw.py](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/scripts/fetch_trials_raw.py)

## Why this comes first

The ingestion pipeline should be understandable in layers:

1. fetch raw source data
2. normalize it
3. validate inclusion or rejection
4. derive helper fields
5. chunk for retrieval
6. store and index

If we combine these too early, it becomes hard to learn what each layer is actually doing.

## Output layout

Each run creates a timestamped directory under [data/raw](/Users/nazeershaikh/Capstone/ai_week/Rag%20Project/data/raw):

```text
data/raw/
└── 20260315T142500Z/
    ├── manifest.json
    └── studies/
        ├── NCT04881760.json
        ├── NCT06318169.json
        └── ...
```

### `manifest.json`

The manifest records:

- the request configuration
- the exact request URLs used
- the returned page counts
- the final list of saved `nct_id` values

This is useful for reproducibility and debugging.

### `studies/*.json`

Each file is the raw study record returned by the API, saved unchanged except for JSON formatting.

This makes the fetcher useful as a learning tool:

- inspect one real record at a time
- compare records across conditions
- verify source field paths before writing the normalizer

## Example usage

Fetch a small obesity batch:

```bash
python3 scripts/fetch_trials_raw.py \
  --query-cond obesity \
  --filter-overall-status RECRUITING \
  --filter-phase PHASE3 \
  --page-size 5 \
  --max-studies 5
```

Fetch a mixed cardiometabolic batch by broad query:

```bash
python3 scripts/fetch_trials_raw.py \
  --query-term "obesity OR type 2 diabetes OR MASH" \
  --page-size 10 \
  --max-studies 10
```

Print the first request URL without making the network call:

```bash
python3 scripts/fetch_trials_raw.py \
  --query-cond "type 2 diabetes" \
  --filter-overall-status RECRUITING \
  --dry-run
```

## Key CLI flags

- `--query-term`: broad free-text query
- `--query-cond`: condition-specific query
- `--query-intr`: intervention query
- `--query-locn`: location query
- `--filter-overall-status`: repeatable status filter
- `--filter-phase`: repeatable phase filter, translated into `filter.advanced`
- `--filter-advanced`: raw ClinicalTrials.gov advanced filter expression
- `--page-size`: studies per API page
- `--max-studies`: hard cap for this run
- `--dry-run`: inspect the request URL only

## Design notes

### Standard library only

The script uses `urllib` instead of `requests`.

Reason:

- no dependency setup yet
- easier to run in a clean environment
- keeps the first ingestion step conceptually small

### One file per study

We could save the entire response as one large file, but per-study files are better for learning and later testing.

Reason:

- easier diffs
- easier manual inspection
- easier to reuse individual studies in unit tests

### Manifest per run

The manifest keeps the fetch stage reproducible without introducing a database too early.

## What comes next

Once we have a few raw records saved locally, the next step is:

- define a minimal Pydantic model for the subset of source fields we consume
- write a one-record normalizer
- compare raw vs normalized output side by side
