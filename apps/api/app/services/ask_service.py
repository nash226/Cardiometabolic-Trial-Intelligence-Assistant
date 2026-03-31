from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.lib.env_utils import load_dotenv

from ..schemas.ask import AskCitation, AskRequest, AskResponse
from ..schemas.fused_search import FusedSearchRequest
from .fused_search_service import fused_search_trials


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def _build_ask_prompt(question: str, citations: list[AskCitation]) -> str:
    evidence_blocks = []
    for citation in citations:
        evidence_blocks.append(
            "\n".join(
                [
                    f"Chunk ID: {citation.chunk_id}",
                    f"Trial: {citation.trial_nct_id}",
                    f"Chunk type: {citation.chunk_type}",
                    f"Title: {citation.title or ''}",
                    f"Source fields: {', '.join(citation.source_field_paths)}",
                    f"Evidence snippet: {citation.snippet}",
                ]
            )
        )

    joined_evidence = "\n\n".join(evidence_blocks)
    return "\n\n".join(
        [
            "You are a clinical trial intelligence assistant.",
            "Answer the question using only the evidence provided.",
            "Do not invent facts or fill missing fields with guesses.",
            "Separate direct evidence from limited inference when necessary.",
            "If the evidence is insufficient, say so plainly.",
            "End with a short Sources line that cites chunk IDs in parentheses.",
            f"Question: {question}",
            f"Evidence:\n{joined_evidence}",
        ]
    )


def _fallback_answer(question: str, citations: list[AskCitation]) -> tuple[str, list[str]]:
    if not citations:
        return (
            "I could not answer from the current corpus because no supporting chunks were retrieved.",
            ["No evidence chunks matched the current query and filters."],
        )

    lines = [
        f"Question: {question}",
        "Retrieved evidence:",
    ]
    for citation in citations[:3]:
        lines.append(
            f"- {citation.trial_nct_id} {citation.chunk_type}: {citation.snippet} ({citation.chunk_id})"
        )
    lines.append("This is an extractive fallback, not a model-generated synthesis.")
    return ("\n".join(lines), ["Returned fallback answer because model synthesis was unavailable."])


def _openai_answer(prompt: str, model: str) -> str:
    load_dotenv(Path.cwd())
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for answer generation.")

    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You answer only from provided trial evidence and keep responses concise.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
    ).encode("utf-8")
    request = Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"OpenAI chat completions HTTP error {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"OpenAI chat completions network error: {exc.reason}") from exc

    choices = payload.get("choices", [])
    if not choices:
        raise RuntimeError("OpenAI chat completions response did not contain choices.")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenAI chat completions response did not contain text content.")
    return content.strip()


def answer_question(request: AskRequest) -> AskResponse:
    fused_response = fused_search_trials(
        FusedSearchRequest(
            query=request.question,
            condition=request.condition,
            phase=request.phase,
            study_type=request.study_type,
            accepted_only=request.accepted_only,
            year_2026_only=request.year_2026_only,
            limit=request.retrieval_limit,
            provider=request.provider,
            model=request.embedding_model,
            lexical_weight=request.lexical_weight,
            semantic_weight=request.semantic_weight,
        )
    )

    citations = [
        AskCitation(
            chunk_id=result.chunk_id,
            trial_nct_id=result.trial_nct_id,
            chunk_type=result.chunk_type,
            title=result.title,
            snippet=result.snippet,
            source_field_paths=result.source_field_paths,
        )
        for result in fused_response.results
    ]

    warnings: list[str] = []
    if not citations:
        answer, fallback_warnings = _fallback_answer(request.question, citations)
        warnings.extend(fallback_warnings)
        return AskResponse(
            question=request.question,
            answer=answer,
            method="extractive_fallback",
            warnings=warnings,
            citations=citations,
        )

    prompt = _build_ask_prompt(request.question, citations)
    try:
        answer = _openai_answer(prompt, request.answer_model)
        method = "grounded_llm"
    except RuntimeError as exc:
        answer, fallback_warnings = _fallback_answer(request.question, citations)
        warnings.extend(fallback_warnings)
        warnings.append(str(exc))
        method = "extractive_fallback"

    return AskResponse(
        question=request.question,
        answer=answer,
        method=method,
        warnings=warnings,
        citations=citations,
    )
