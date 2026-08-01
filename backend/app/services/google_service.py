"""Google integration (one OAuth) — Gmail send + Google Calendar.

Single-user (one rep) POC: the connected account's OAuth credentials live in one
`GoogleToken` row. Everything is gated by `settings.google_configured` (an OAuth
client is set) and a stored token (a Google account is linked).

`settings.mock_google` short-circuits every network call with deterministic canned
data so tests / Playwright never contact Google.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import List, Optional

# Allow the http://localhost dev redirect and tolerate Google re-ordering scopes.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

from sqlmodel import Session, select

from app import models
from app.config import settings
from app.db import engine

# One consent covers identifying the account, sending mail, and calendar events.
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]


# --------------------------------------------------------------------------- #
# Token store (single row)
# --------------------------------------------------------------------------- #
def _get_token_row(session: Session) -> Optional[models.GoogleToken]:
    return session.exec(select(models.GoogleToken)).first()


def _save_token(
    session: Session,
    *,
    email: Optional[str],
    access_token: Optional[str],
    refresh_token: Optional[str],
    scopes: List[str],
    expiry: Optional[datetime],
) -> None:
    row = _get_token_row(session)
    if row is None:
        row = models.GoogleToken()
    row.google_email = email or row.google_email
    row.access_token = access_token
    # Google only returns a refresh_token on the first consent — keep the old one.
    if refresh_token:
        row.refresh_token = refresh_token
    row.scopes = " ".join(scopes or [])
    row.token_expiry = expiry
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()


def is_connected() -> bool:
    if settings.mock_google:
        return True
    with Session(engine) as session:
        row = _get_token_row(session)
        return bool(row and row.refresh_token)


def status() -> dict:
    if settings.mock_google:
        return {"configured": True, "connected": True,
                "email": "mock@calendar.test", "scopes": GOOGLE_SCOPES}
    with Session(engine) as session:
        row = _get_token_row(session)
    connected = bool(row and row.refresh_token)
    return {
        "configured": settings.google_configured,
        "connected": connected,
        "email": row.google_email if connected else None,
        "scopes": (row.scopes.split() if (connected and row.scopes) else []),
    }


def disconnect() -> None:
    with Session(engine) as session:
        row = _get_token_row(session)
        if row is not None:
            session.delete(row)
            session.commit()


# --------------------------------------------------------------------------- #
# OAuth flow
# --------------------------------------------------------------------------- #
def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def _build_flow(state: Optional[str] = None):
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        _client_config(),
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.google_redirect_uri,
        state=state,
    )
    # Disable PKCE: the login and callback are separate stateless requests, so the
    # auto-generated code_verifier can't survive between them ("Missing code
    # verifier" at token exchange). A confidential web client authenticates the
    # exchange with its client_secret, so PKCE isn't required.
    flow.autogenerate_code_verifier = False
    return flow


# --------------------------------------------------------------------------- #
# OAuth CSRF state (signed + time-bounded, stateless — no session store needed)
# --------------------------------------------------------------------------- #
def _state_secret() -> bytes:
    """Key for signing the OAuth `state`. Derived from the client secret so it is
    stable across the separate login and callback requests without a session store;
    falls back to a fixed dev string when no client secret is configured."""
    base = (settings.google_client_secret or "salesintel-dev-state").encode()
    return hashlib.sha256(base).digest()


def make_state() -> str:
    """A signed, timestamped state nonce embedded in the consent URL."""
    msg = f"{secrets.token_urlsafe(12)}.{int(time.time())}"
    sig = hmac.new(_state_secret(), msg.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{msg}.{sig}"


def verify_state(state: str, max_age_seconds: int = 600) -> bool:
    """True iff `state` was minted by make_state() within the last max_age_seconds."""
    parts = (state or "").split(".")
    if len(parts) != 3:
        return False
    nonce, ts, sig = parts
    expected = hmac.new(_state_secret(), f"{nonce}.{ts}".encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        age = int(time.time()) - int(ts)
    except ValueError:
        return False
    return 0 <= age <= max_age_seconds


def authorization_url() -> str:
    """The Google consent URL to redirect the browser to."""
    flow = _build_flow()
    url, _ = flow.authorization_url(
        access_type="offline",          # get a refresh_token
        include_granted_scopes="true",
        prompt="consent",               # force refresh_token even on re-connect
        state=make_state(),             # CSRF: validated in the callback
    )
    return url


def exchange_code(code: str) -> str:
    """Exchange the callback code for tokens, store them, return the account email."""
    flow = _build_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    email = _fetch_email(creds)
    with Session(engine) as session:
        _save_token(
            session,
            email=email,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            scopes=list(creds.scopes or GOOGLE_SCOPES),
            expiry=creds.expiry,
        )
    return email or ""


def _credentials():
    """Load stored credentials, refreshing the access token if expired."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    with Session(engine) as session:
        row = _get_token_row(session)
        if row is None or not row.refresh_token:
            raise RuntimeError("Google is not connected.")
        creds = Credentials(
            token=row.access_token,
            refresh_token=row.refresh_token,
            token_uri=row.token_uri,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=(row.scopes.split() if row.scopes else GOOGLE_SCOPES),
        )
        if not creds.valid:
            creds.refresh(Request())
            row.access_token = creds.token
            row.token_expiry = creds.expiry
            row.updated_at = datetime.utcnow()
            session.add(row)
            session.commit()
        return creds


def _fetch_email(creds) -> Optional[str]:
    try:
        from googleapiclient.discovery import build

        info = build("oauth2", "v2", credentials=creds, cache_discovery=False).userinfo().get().execute()
        return info.get("email")
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Calendar
# --------------------------------------------------------------------------- #
def _rfc3339(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def list_events(days_back: int = 1, days_ahead: int = 30, max_results: int = 50) -> List[dict]:
    """Upcoming primary-calendar events as simplified dicts."""
    if settings.mock_google:
        return _mock_events()
    from googleapiclient.discovery import build

    now = datetime.now(timezone.utc)
    service = build("calendar", "v3", credentials=_credentials(), cache_discovery=False)
    resp = service.events().list(
        calendarId="primary",
        timeMin=_rfc3339(now - timedelta(days=days_back)),
        timeMax=_rfc3339(now + timedelta(days=days_ahead)),
        singleEvents=True,
        orderBy="startTime",
        maxResults=max_results,
    ).execute()
    out: List[dict] = []
    for e in resp.get("items", []):
        start = e.get("start", {})
        out.append({
            "id": e.get("id"),
            "summary": e.get("summary", "") or "(no title)",
            "start": start.get("dateTime") or start.get("date"),
            "html_link": e.get("htmlLink"),
            "description": e.get("description", ""),
            "attendees": [a.get("email", "") for a in e.get("attendees", [])],
        })
    return out


def insert_event(*, summary: str, start: datetime, description: str = "",
                 duration_minutes: int = 30) -> dict:
    """Create an event on the primary calendar; returns {id, html_link}."""
    if settings.mock_google:
        return {"id": "mock-created-event", "html_link": "https://calendar.google.com/mock"}
    from googleapiclient.discovery import build

    service = build("calendar", "v3", credentials=_credentials(), cache_discovery=False)
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": _rfc3339(start)},
        "end": {"dateTime": _rfc3339(start + timedelta(minutes=duration_minutes))},
    }
    ev = service.events().insert(calendarId="primary", body=body).execute()
    return {"id": ev.get("id"), "html_link": ev.get("htmlLink")}


# --------------------------------------------------------------------------- #
# Gmail
# --------------------------------------------------------------------------- #
def send_message(*, to: str, subject: str, html: str, plain: str = "",
                 attachment_bytes: Optional[bytes] = None,
                 attachment_filename: Optional[str] = None,
                 attachment_maintype: str = "application",
                 attachment_subtype: str = "pdf") -> str:
    """Send an email as the connected Gmail account; returns the sent message id."""
    if settings.mock_google:
        return "mock-sent-message"
    from googleapiclient.discovery import build

    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(plain or "See the HTML version of this brief.")
    msg.add_alternative(html, subtype="html")
    if attachment_bytes and attachment_filename:
        msg.add_attachment(attachment_bytes, maintype=attachment_maintype,
                           subtype=attachment_subtype, filename=attachment_filename)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service = build("gmail", "v1", credentials=_credentials(), cache_discovery=False)
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent.get("id", "")


# --------------------------------------------------------------------------- #
# Mock data (settings.mock_google)
# --------------------------------------------------------------------------- #
def _mock_events() -> List[dict]:
    base = datetime(2026, 8, 1, 10, 30, tzinfo=timezone.utc)
    return [
        {
            "id": "mock-evt-sleep",
            "summary": "Discovery call with The Sleep Company",
            "start": base.isoformat(),
            "html_link": "https://calendar.google.com/mock/sleep",
            "description": "Intro + scaling omnichannel support.",
            "attendees": ["rep@zoho.com", "vp@thesleepcompany.in"],
        },
        {
            "id": "mock-evt-standup",
            "summary": "Team standup",
            "start": (base + timedelta(days=1)).isoformat(),
            "html_link": "https://calendar.google.com/mock/standup",
            "description": "",
            "attendees": [],
        },
    ]
