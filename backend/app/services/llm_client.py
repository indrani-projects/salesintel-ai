"""Shared OpenAI-compatible LLM client helper (AI-Engine Agent).

Builds an `openai.OpenAI` client pointed at `settings.llm_base_url` with
`settings.llm_api_key`, and exposes the configured model name. Works against any
OpenAI-compatible endpoint (default: Gemini free tier).
"""
from __future__ import annotations

from app.config import settings


def get_client():
    """Return an OpenAI-compatible client configured from settings."""
    from openai import OpenAI

    return OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key or "missing-key",
    )


def get_model() -> str:
    return settings.llm_model
