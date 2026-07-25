"""
SalesIntel_AI — API contract (Phase-0, Lead-authored).

This module is the SHARED CONTRACT between all three subagents. It is treated as
READ-ONLY by the Backend, AI-Engine, and Frontend agents. Do not change field
names or types without updating the plan and notifying the Lead — the frontend
TypeScript client and the AI-engine JSON output both mirror these shapes exactly.

All API request/response bodies are defined here as Pydantic models.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class BriefStatus(str, Enum):
    pending = "pending"        # meeting created, generation not started
    generating = "generating"  # brief is being synthesized
    ready = "ready"            # brief available
    error = "error"            # generation failed


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"  # rendered as "verify before use"


class Persona(str, Enum):
    # The six personas from docs/shared/Expected_Features_By_Persona. Each reframes
    # the prospect brief to that reader's goals.
    sales_rep = "sales_rep"          # Sales Representative — full pre-meeting brief
    sales_manager = "sales_manager"  # Sales Manager — coaching lens
    enablement = "enablement"        # Sales Enablement — best-practice / onboarding lens
    revops = "revops"                # Revenue Operations Manager — ROI / adoption lens
    vp_sales = "vp_sales"            # VP of Sales — executive lens
    admin = "admin"                  # SalesIntel AI Admin — data provenance / quality lens


# The nine fixed sections of every brief, in display order.
SECTION_ORDER: List[str] = [
    "company_snapshot",
    "financials",
    "trigger_events",
    "gtm_model",
    "pain_hypotheses",
    "tech_stack",
    "stakeholders",
    "risks",
    "recommended_angle",
]

SECTION_TITLES = {
    "company_snapshot": "Company Snapshot",
    "financials": "Financial & Funding Health",
    "trigger_events": "Trigger Events / Recent News",
    "gtm_model": "GTM & Operating Model",
    "pain_hypotheses": "Pain Hypotheses → Mapped to Zoho",
    "tech_stack": "Tech Stack Signals",
    "stakeholders": "Key Stakeholders",
    "risks": "Risks & Watch-outs",
    "recommended_angle": "Analyst's Recommended Angle",
}

# --------------------------------------------------------------------------- #
# Persona metadata + per-persona section sets
# --------------------------------------------------------------------------- #
PERSONA_LABELS = {
    "sales_rep": "Sales Representative",
    "sales_manager": "Sales Manager",
    "enablement": "Sales Enablement",
    "revops": "Revenue Operations Manager",
    "vp_sales": "VP of Sales",
    "admin": "SalesIntel AI Admin",
}

PERSONA_TAGLINES = {
    "sales_rep": "Prepare fast for every customer meeting",
    "sales_manager": "Coach the team, improve win rates",
    "enablement": "Standardize prep, accelerate onboarding",
    "revops": "Drive adoption and prove ROI",
    "vp_sales": "Measure business impact and revenue growth",
    "admin": "Secure, reliable platform operations",
}

# Ordered (id, title) sections for each persona's brief. Sales Representative reuses
# the full nine-section brief (SECTION_ORDER); the rest reframe it to their lens.
PERSONA_SECTIONS = {
    "sales_rep": [(sid, SECTION_TITLES[sid]) for sid in SECTION_ORDER],
    "sales_manager": [
        ("deal_snapshot", "Deal Snapshot"),
        ("coaching_focus", "Coaching Focus"),
        ("deal_risks", "Deal Risks & Watch-outs"),
        ("key_stakeholders", "Key Stakeholders"),
        ("rep_questions", "Questions to Ask Your Rep"),
        ("next_steps", "Recommended Next Steps"),
    ],
    "enablement": [
        ("company_snapshot", "Company Snapshot"),
        ("best_practice_prep", "Best-Practice Prep Steps"),
        ("talking_points", "Key Talking Points"),
        ("objection_handling", "Objection Handling"),
        ("playbook_alignment", "Playbook & Messaging Alignment"),
        ("readiness_checklist", "Pre-Meeting Readiness Checklist"),
    ],
    "revops": [
        ("account_snapshot", "Account Snapshot"),
        ("data_health", "CRM Data Health & Gaps"),
        ("process_fit", "Process & Workflow Fit"),
        ("automation_opportunities", "Automation Opportunities"),
        ("roi_hypothesis", "ROI Hypothesis"),
        ("adoption_angle", "Adoption & Rollout Angle"),
    ],
    "vp_sales": [
        ("executive_summary", "Executive Summary"),
        ("strategic_fit", "Strategic Fit"),
        ("revenue_opportunity", "Revenue Opportunity"),
        ("win_risk", "Win Probability & Risks"),
        ("competitive_landscape", "Competitive Landscape"),
        ("exec_recommendation", "Executive Recommendation"),
    ],
    "admin": [
        ("source_inventory", "Source Inventory & Credibility"),
        ("data_lineage", "Data Lineage — Fact → Source"),
        ("coverage_gaps", "Coverage Gaps & Missing Data"),
        ("data_freshness", "Data Freshness"),
        ("integration_status", "Integration & Field-Mapping Status"),
        ("quality_flags", "Quality Flags & Watch-outs"),
    ],
}

# The default persona (also the frontend's initial selection).
DEFAULT_PERSONA = "sales_rep"


def sections_for(persona: str):
    """Ordered [(id, title), ...] for a persona (defaults to Sales Representative)."""
    return PERSONA_SECTIONS.get(persona, PERSONA_SECTIONS[DEFAULT_PERSONA])


# --------------------------------------------------------------------------- #
# Companies (prospect dropdown)
# --------------------------------------------------------------------------- #
class CompanyRead(BaseModel):
    slug: str            # e.g. "sleep_company" (folder name under docs/)
    name: str            # e.g. "The Sleep Company"
    doc_count: int       # number of source docs available


# --------------------------------------------------------------------------- #
# Meetings
# --------------------------------------------------------------------------- #
class MeetingCreate(BaseModel):
    subject: str = Field(..., examples=["Discovery call with The Sleep Company"])
    prospect_company: str = Field(..., examples=["The Sleep Company"])
    why: str = Field("", description="Why this meeting / what we want from it")
    agenda: str = Field("", description="Agenda; steers which angle the brief emphasizes")
    start_time: datetime
    persona: Persona = Field(Persona.sales_rep, description="Primary rep persona for this meeting")


class MeetingRead(BaseModel):
    id: int
    subject: str
    prospect_company: str
    company_slug: Optional[str] = None
    why: str
    agenda: str
    start_time: datetime
    created_at: datetime
    brief_status: BriefStatus
    persona: Persona = Persona.sales_rep  # the meeting's primary persona
    google_event_id: Optional[str] = None   # set when linked to a Google Calendar event
    google_html_link: Optional[str] = None   # deep-link to the event on Google


# --------------------------------------------------------------------------- #
# Brief content (the AI-Engine's structured output)
# --------------------------------------------------------------------------- #
class BriefSource(BaseModel):
    """A citable source. `marker` is referenced inline in section content, e.g. [S1]."""
    marker: str                      # "S1", "S2", ...
    title: str                       # human title of the source
    filename: Optional[str] = None   # source file under docs/<company>/
    url: Optional[str] = None        # original URL if known


class BriefSection(BaseModel):
    id: str                          # one of SECTION_ORDER
    title: str                       # display title (see SECTION_TITLES)
    content_md: str                  # markdown; may contain inline [S1] citation markers
    confidence: Confidence = Confidence.high
    flags: List[str] = Field(default_factory=list)  # e.g. ["verify before use"]


class KeyFact(BaseModel):
    """A headline metric for the at-a-glance KPI strip (e.g. ARR / funding / scale)."""
    label: str
    value: str
    note: Optional[str] = None


class BriefContent(BaseModel):
    """A persona-shaped brief. Stored as JSON on the Brief row. The AI-Engine
    returns the section set defined by PERSONA_SECTIONS[persona], in order."""
    company: str
    company_slug: str
    persona: Persona = Persona.sales_rep
    headline: str = ""               # one-line TL;DR shown at top
    key_facts: List[KeyFact] = Field(default_factory=list)  # 3-5 at-a-glance metrics
    sections: List[BriefSection]
    sources: List[BriefSource]
    generated_at: Optional[datetime] = None


class BriefRead(BaseModel):
    """What GET /meetings/{id}/brief returns (for a given persona)."""
    meeting_id: int
    persona: Persona = Persona.sales_rep
    status: BriefStatus
    content: Optional[BriefContent] = None   # present when status == ready
    html: Optional[str] = None               # rendered HTML (brief_render), when ready
    error: Optional[str] = None              # present when status == error


# --------------------------------------------------------------------------- #
# Chat
# --------------------------------------------------------------------------- #
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer_md: str                   # markdown answer, may contain [S1] markers
    citations: List[BriefSource] = Field(default_factory=list)
    grounded: bool = True            # False when the answer isn't supported by sources


class ChatMessageRead(BaseModel):
    id: int
    meeting_id: int
    role: str                        # "user" | "assistant"
    content: str
    created_at: datetime


# --------------------------------------------------------------------------- #
# Email ("Send as email")
# --------------------------------------------------------------------------- #
class EmailPreview(BaseModel):
    """The composed email for a persona brief, for in-app review before sending."""
    subject: str
    body_html: str                   # persona-tailored digest (inline-styled HTML)
    attachment_filename: str         # the full brief attached as a .html file
    recipient_default: str = ""      # prefills the To: field
    email_configured: bool = False   # True → a real email will be sent on confirm


class EmailSendRequest(BaseModel):
    recipient: str


class EmailSendResult(BaseModel):
    delivered: bool                  # True only when a real email was actually sent
    mode: str                        # "sent" | "demo" | "error"
    recipient: str
    subject: str
    message: str                     # human-readable status for the UI


class EmailAutomationStatus(BaseModel):
    """Read-only view of the auto-email settings, for the Settings page."""
    enabled: bool = False            # AUTO_EMAIL_ENABLED — sends on-ready + reminder
    lead_minutes: int = 60           # reminder fires this long before start_time
    recipient: str = ""              # default_recipient (blank ⇒ auto-send skipped)
    transport: str = "demo"          # "gmail" | "smtp" | "demo" — how a send delivers
    day_before_enabled: bool = False  # also send the brief ~this long before the meeting
    day_before_minutes: int = 1440    # day-before window (default 24h)
    personalized: bool = False        # True ⇒ some personas have their own recipient email


# --------------------------------------------------------------------------- #
# Google integration (one OAuth: Gmail send + Calendar)
# --------------------------------------------------------------------------- #
class GoogleStatus(BaseModel):
    configured: bool = False          # OAuth client set in .env (Connect is possible)
    connected: bool = False           # a Google account is linked (token stored)
    email: Optional[str] = None       # the connected Google account
    scopes: List[str] = Field(default_factory=list)


class CalendarSyncResult(BaseModel):
    imported: int = 0                 # new meetings created from Google events
    briefed: int = 0                  # of those, matched a prospect → brief queued
    skipped_existing: int = 0         # events already imported (deduped)
    scanned: int = 0                  # total Google events looked at
    message: str = ""


# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #
class HealthResponse(BaseModel):
    status: str = "ok"
    llm_configured: bool = False
