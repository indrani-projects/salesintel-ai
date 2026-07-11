"""
App settings (Phase-0, Lead-authored — SHARED, read-only for agents).

Both the Backend Agent and AI-Engine Agent import `settings` from here.
Values come from backend/.env (see .env.example). Env var names are
upper-snake (LLM_BASE_URL) and map case-insensitively to the fields below.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (OpenAI-compatible; default = Gemini free tier)
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: str = ""

    # App
    database_url: str = "sqlite:///./salesintel.db"
    docs_root: str = "../docs"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # When true, the brief engine and Scout return deterministic canned output
    # instead of calling the LLM — used by tests and Playwright E2E so they are
    # fast, repeatable, and don't consume Gemini free-tier quota.
    mock_llm: bool = False

    @property
    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_configured(self) -> bool:
        key = (self.llm_api_key or "").strip()
        return bool(key) and "PASTE" not in key

    @property
    def docs_root_path(self) -> Path:
        p = Path(self.docs_root)
        return p if p.is_absolute() else (BASE_DIR / p).resolve()


settings = Settings()
