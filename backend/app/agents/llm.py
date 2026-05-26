"""Thin Gemini wrapper. Centralizing here keeps prompt/agent code clean and makes
swapping providers a one-file change."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import google.generativeai as genai

from app.config import settings

log = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)


def _chat_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(settings.gemini_chat_model)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def chat_text(system: str, user: str, temperature: float = 0.4) -> str:
    model = _chat_model()
    prompt = f"{system}\n\n---\n\n{user}"
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": temperature},
    )
    return (resp.text or "").strip()


def chat_json(system: str, user: str, temperature: float = 0.2) -> Any:
    """Ask Gemini for JSON. We use response_mime_type to force JSON output."""
    model = _chat_model()
    prompt = f"{system}\n\nReturn ONLY valid JSON, no prose, no markdown.\n\n---\n\n{user}"
    resp = model.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    )
    raw = (resp.text or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _strip_code_fence(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            log.warning("LLM returned non-JSON, raw=%r", raw[:400])
            raise ValueError(f"LLM did not return valid JSON: {e}") from e


EMBED_DIM = 768  # matches the pgvector column in app/models/feedback.py


def embed(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Batch-embed texts. Returns EMBED_DIM (=768) vectors.

    Current model: `gemini-embedding-001` (the default `text-embedding-004` was
    sunset in v1beta). The newer model is 3072-dim by default but supports
    `output_dimensionality` to truncate — we keep 768 so it matches our DB schema."""
    if not texts:
        return []
    out: list[list[float]] = []
    BATCH = 100
    for i in range(0, len(texts), BATCH):
        chunk = texts[i : i + BATCH]
        resp = genai.embed_content(
            model=f"models/{settings.gemini_embed_model}",
            content=chunk,
            task_type=task_type,
            output_dimensionality=EMBED_DIM,
        )
        emb = resp["embedding"]
        if emb and isinstance(emb[0], (int, float)):
            out.append(list(emb))  # single vector
        else:
            out.extend([list(v) for v in emb])
    return out
