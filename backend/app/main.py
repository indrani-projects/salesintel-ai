"""
SalesIntel AI — FastAPI application entrypoint.
"""
from __future__ import annotations

import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import briefs, chat, google, meetings
from app.config import settings
from app.db import init_db
from app.schemas import HealthResponse

app = FastAPI(title="SalesIntel AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router)
app.include_router(briefs.router)
app.include_router(chat.router)
app.include_router(google.router)


def _startup_sync_and_generate() -> None:
    """Runs once at boot, off the request path (its own thread) so it never delays
    server start: (1) requeue any brief a prior process left mid-'generating',
    (2) sync Google Calendar (import only) if connected, (3) generate all queued
    briefs in the background, earliest meeting first. Fully fail-soft."""
    try:
        requeued = meetings.reset_stale_generating()
        if requeued:
            print(f"[startup] requeued {requeued} stale brief(s)", flush=True)
    except Exception as exc:  # noqa: BLE001 — never block startup
        print(f"[startup] reset_stale_generating failed: {exc}", flush=True)

    try:
        if google.google_service.is_connected():
            scanned, imported, updated, skipped = google.import_calendar_events()
            print(
                f"[startup] calendar sync: scanned {scanned}, imported {imported}, "
                f"updated {updated}, skipped {skipped}",
                flush=True,
            )
    except Exception as exc:  # noqa: BLE001 — never block startup
        print(f"[startup] calendar sync failed: {exc}", flush=True)

    try:
        meetings.generate_pending_briefs()
    except Exception as exc:  # noqa: BLE001
        print(f"[startup] brief generation failed: {exc}", flush=True)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    if settings.sync_on_startup:
        # Sync + generation run in a daemon thread so uvicorn finishes binding the
        # port immediately; briefs fill in afterwards (status is polled by the UI).
        threading.Thread(target=_startup_sync_and_generate, daemon=True).start()
    if settings.auto_email_enabled:
        # Long-lived reminder scheduler: emails each brief ~1h before its meeting.
        from app.services import notifier

        threading.Thread(target=notifier.reminder_loop, daemon=True).start()
    if settings.calendar_sync_enabled:
        # Long-lived scheduler: re-import Google Calendar prospect events every
        # `calendar_sync_seconds` so meetings added in Google appear automatically.
        threading.Thread(target=google.calendar_sync_loop, daemon=True).start()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", llm_configured=settings.llm_configured)
