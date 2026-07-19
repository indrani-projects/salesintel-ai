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

    # ---- Email ("Send as email") ----
    # Real delivery happens only when SMTP is configured AND mock_email is off.
    # With no SMTP creds (the default) the feature runs in "demo send": the email
    # is composed + previewed + confirmed, but nothing leaves the machine.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""              # falls back to smtp_user when blank
    default_recipient: str = ""      # prefills the dialog's To: field
    # When true, force demo-send even if SMTP is configured — used by tests/E2E so
    # verification never contacts a real mail server.
    mock_email: bool = False

    # ---- Google (one OAuth: Gmail send + Calendar) ----
    # Create an OAuth client at console.cloud.google.com (see .env.example /
    # docs/RUNBOOK). Redirect URI must match the registered one exactly.
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    # Where the OAuth callback sends the browser back to (the app's Settings page).
    frontend_url: str = "http://localhost:5173"
    # When true, google_service returns canned events / no-op send — used by tests
    # and E2E so verification never contacts Google.
    mock_google: bool = False
    # On server start, auto-sync the calendar (import only) and then generate any
    # queued briefs in the background, earliest meeting first. Off in tests/E2E so
    # the explicit-sync assertions run against a clean, un-raced DB.
    sync_on_startup: bool = True

    # ---- Automated brief emails ----
    # When on, a meeting's brief is emailed automatically as soon as it's ready, and
    # again `reminder_lead_minutes` before the meeting start_time. Recipient is
    # `default_recipient`; delivery uses the same Gmail/SMTP/demo path as manual send.
    # Master switch — off in tests/E2E so the on-ready hook and the reminder daemon
    # can't interfere with deterministic assertions.
    auto_email_enabled: bool = True
    reminder_lead_minutes: int = 60   # send the reminder this long before start_time
    reminder_poll_seconds: int = 60   # how often the reminder scheduler wakes up

    # ---- Web prospect intel (fetch news / SEC filings / social by company name) ----
    # On meeting creation the brief pulls live web intel for the prospect, keyword-
    # filters it (no LLM), caches the filtered text, and feeds it to the brief + Scout.
    # Falls back to docs/<company>/ when the web returns nothing.
    web_intel_enabled: bool = True
    web_ttl_hours: int = 24          # cached filtered-intel freshness
    web_max_chars: int = 6000        # cap on cached text per source
    # When true, web_sources returns deterministic canned intel — tests/E2E, no network.
    mock_web: bool = False

    @property
    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_configured(self) -> bool:
        key = (self.llm_api_key or "").strip()
        return bool(key) and "PASTE" not in key

    @property
    def email_configured(self) -> bool:
        """True when enough SMTP settings exist to attempt a real send."""
        return bool(
            self.smtp_host.strip()
            and self.smtp_user.strip()
            and self.smtp_password.strip()
        )

    @property
    def email_from(self) -> str:
        return (self.smtp_from or self.smtp_user).strip()

    @property
    def google_configured(self) -> bool:
        """True when an OAuth client is set (so the Connect flow can run)."""
        return bool(self.google_client_id.strip() and self.google_client_secret.strip())

    @property
    def docs_root_path(self) -> Path:
        p = Path(self.docs_root)
        return p if p.is_absolute() else (BASE_DIR / p).resolve()


settings = Settings()
