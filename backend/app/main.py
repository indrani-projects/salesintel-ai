"""
SalesIntel AI — FastAPI application entrypoint.
"""
from __future__ import annotations

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


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", llm_configured=settings.llm_configured)
