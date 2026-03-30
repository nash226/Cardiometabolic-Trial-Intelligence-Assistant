#!/usr/bin/env python3
"""Build a simple lexical index over chunk files."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9_+-]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a lexical index from chunk JSON files."
    )
    parser.add_argument(
        "chunks_dir",
        type=Path,
        help="Directory containing chunk JSON files.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_lexical_index.json",
        help="Output path for the built index.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def build_index(chunks_dir: Path) -> dict[str, Any]:
    postings: dict[str, dict[str, int]] = defaultdict(dict)
    chunk_store: dict[str, dict[str, Any]] = {}
    chunk_files = sorted(chunks_dir.glob("*.json"))

    for chunk_file in chunk_files:
        payload = load_json(chunk_file)
        for chunk in payload.get("chunks", []):
            if not isinstance(chunk, dict):
                continue
            chunk_id = chunk.get("chunk_id")
            content = chunk.get("content", "")
            if not isinstance(chunk_id, str) or not isinstance(content, str):
                continue

            tokens = tokenize(content)
            token_counts = Counter(tokens)
            chunk_store[chunk_id] = {
                "chunk_id": chunk_id,
                "trial_nct_id": chunk.get("trial_nct_id"),
                "chunk_type": chunk.get("chunk_type"),
                "title": chunk.get("title"),
                "content": content,
                "source_field_paths": chunk.get("source_field_paths", []),
                "token_count_estimate": chunk.get("token_count_estimate"),
            }
            for token, count in token_counts.items():
                postings[token][chunk_id] = count

    return {
        "chunk_count": len(chunk_store),
        "token_count": len(postings),
        "chunks_dir": str(chunks_dir),
        "postings": postings,
        "chunk_store": chunk_store,
    }


def main() -> int:
    args = parse_args()
    index = build_index(args.chunks_dir)
    write_json(args.output_path, index)
    print(f"Built chunk index at {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
