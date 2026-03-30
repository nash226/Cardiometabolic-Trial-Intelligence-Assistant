#!/usr/bin/env python3
"""Build a semantic embeddings index over chunk files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lib.embedding_utils import embed_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build chunk embeddings for semantic search."
    )
    parser.add_argument("chunks_dir", type=Path, help="Directory containing chunk JSON files.")
    parser.add_argument(
        "--provider",
        choices=["local_debug", "openai"],
        default="local_debug",
        help="Embedding provider to use.",
    )
    parser.add_argument(
        "--model",
        help="Embedding model name. Required when provider=openai.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data") / "indexes" / "chunk_semantic_index.json",
        help="Output path for the semantic index.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_semantic_index(chunks_dir: Path, provider: str, model: str | None) -> dict[str, Any]:
    chunk_store: dict[str, dict[str, Any]] = {}
    embeddings: dict[str, list[float]] = {}

    for chunk_file in sorted(chunks_dir.glob("*.json")):
        payload = load_json(chunk_file)
        for chunk in payload.get("chunks", []):
            if not isinstance(chunk, dict):
                continue
            chunk_id = chunk.get("chunk_id")
            content = chunk.get("content")
            if not isinstance(chunk_id, str) or not isinstance(content, str):
                continue

            chunk_store[chunk_id] = {
                "chunk_id": chunk_id,
                "trial_nct_id": chunk.get("trial_nct_id"),
                "chunk_type": chunk.get("chunk_type"),
                "title": chunk.get("title"),
                "content": content,
                "source_field_paths": chunk.get("source_field_paths", []),
                "token_count_estimate": chunk.get("token_count_estimate"),
            }
            embeddings[chunk_id] = embed_text(content, provider=provider, model=model)

    return {
        "provider": provider,
        "model": model,
        "chunk_count": len(chunk_store),
        "chunks_dir": str(chunks_dir),
        "chunk_store": chunk_store,
        "embeddings": embeddings,
    }


def main() -> int:
    args = parse_args()
    index = build_semantic_index(args.chunks_dir, provider=args.provider, model=args.model)
    write_json(args.output_path, index)
    print(f"Built semantic index at {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
