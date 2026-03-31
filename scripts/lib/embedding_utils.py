"""Embedding helpers for semantic chunk retrieval."""

from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path
from typing import Any

try:
    from .env_utils import load_dotenv
except ImportError as exc:  # pragma: no cover - script execution fallback
    if __package__ not in (None, ""):
        raise
    from lib.env_utils import load_dotenv

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - dependency missing at runtime
    OpenAI = Any  # type: ignore[assignment]
    OPENAI_IMPORT_ERROR = exc
else:
    OPENAI_IMPORT_ERROR = None


TOKEN_PATTERN = re.compile(r"[a-z0-9_+-]+")
LOCAL_DEBUG_DIMENSION = 256


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same length for cosine similarity")
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def local_debug_embedding(text: str, dimension: int = LOCAL_DEBUG_DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    tokens = tokenize(text)
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


def openai_embedding(text: str, model: str) -> list[float]:
    if OPENAI_IMPORT_ERROR is not None:
        raise RuntimeError(
            "The openai package is required for provider=openai. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from OPENAI_IMPORT_ERROR

    load_dotenv(Path.cwd())
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for provider=openai")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=model, input=text)
    data = getattr(response, "data", None)
    if not data:
        raise RuntimeError("OpenAI embeddings response did not contain data")
    embedding = data[0].embedding
    if not isinstance(embedding, list):
        raise RuntimeError("OpenAI embeddings response did not contain an embedding list")
    return [float(value) for value in embedding]


def embed_text(text: str, provider: str, model: str | None = None) -> list[float]:
    if provider == "local_debug":
        return local_debug_embedding(text)
    if provider == "openai":
        if not model:
            raise RuntimeError("A model must be provided when provider=openai")
        return openai_embedding(text, model)
    raise ValueError(f"Unsupported embedding provider: {provider}")
