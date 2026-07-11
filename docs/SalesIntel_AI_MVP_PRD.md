# SalesIntel AI — MVP Product Requirements Document
**Phase 2 Deliverable — Team COSMOS**
**Scope: P0 / MVP only (Month 0–3), per Phase 1 Strategic Roadmap**

---

## 1. Purpose of this document

Phase 1 established *why* SalesIntel AI should exist and *who* it's for. This document defines *what we are actually building for the demo* — the MVP, its architecture, and the requirements an engineering team would need to ship it. It intentionally excludes everything Phase 1 marked as P1/P2/P3 (Slack delivery, CRM integrations, SSO, mobile, etc.) so the demo stays honest to a real 0–3 month build.

---

## 2. Problem statement (recap)

B2B SaaS Account Executives lose 30–60 minutes per meeting manually assembling context across 7+ disconnected tools (LinkedIn, CRM, Google News, Crunchbase, G2, Slack, email). There is no synthesis layer. This is the "pre-meeting intelligence gap." At a 50-rep org, this costs ~225 hours/week (~$675K/year in lost productivity).

**MVP hypothesis to test:** *Will a sales rep consistently read an AI-generated brief before a meeting if it requires zero effort to receive?*

Everything in this PRD exists to test that one hypothesis as cheaply and quickly as possible — using only public data, no CRM integration, no Slack.

---

## 3. Goals & non-goals

### MVP goals
- Auto-detect an upcoming sales meeting from the rep's calendar with zero manual input
- Generate an AI brief (stakeholder context, account news, talking points) grounded only in public sources
- Deliver the brief via email with a one-click web view, in time for the rep to read it before the meeting
- Prove the core habit: reps open and use the brief

### Non-goals (explicitly out of scope for MVP)
- CRM integration (Salesforce/HubSpot) — Phase 1 (P1)
- Slack delivery — Phase 1 (P1)
- Trigger-event alerts, Manager Dashboard — Phase 1 (P1)
- SSO/SAML, SOC 2 — Phase 2 (P2)
- In-brief customization, RevOps analytics — Phase 2 (P2)
- Mobile app, multi-language, pre-pipeline signal engine — Phase 3 (P3)

---

## 4. Primary persona for MVP

**Rohan M. — B2B SaaS Account Executive**, 24–35, mid-market SaaS company (100–600 employees), 20–60 meetings/month, high tech proficiency, low tolerance for new logins.

> *"I open my SalesIntel brief on the way to my desk — 25 min before the call, fully prepped, zero tabs open."*

Design constraint this implies: **the MVP must not require Rohan to log into a new tool to get value.** Email delivery + one-click web view satisfies this; a native app or dashboard he must remember to check does not.

---

## 5. MVP scope — the three P0 features

| # | Feature | Description | Data sources | Status |
|---|---|---|---|---|
| 1 | AI Brief Generation | Core engine that synthesizes stakeholder info, account news, and talking points into a structured brief | LinkedIn, Google News, Crunchbase, G2 (public only) | Build now |
| 2 | Calendar Integration | Auto-detects meetings on Google/Outlook calendar and triggers brief generation with zero rep action | Google Calendar API, Microsoft Graph API | Build now |
| 3 | Email Delivery | Delivers brief to rep's inbox with a one-click web view link; no new login required | Transactional email (e.g. SendGrid/SES) + hosted web view | Build now |

**Why these three and nothing else:** they are the only things that test the core hypothesis. Every other feature (CRM sync, Slack, dashboards) is only worth building if reps actually open a zero-effort brief. If Brief Click-Through Rate doesn't clear 65% by Day 60, the fix is to iterate on brief quality and delivery — not to add features we haven't built yet.

---

## 6. System architecture (see diagram above)

### 6.1 Component breakdown

**1. Calendar trigger service**
- OAuth connection to Google Calendar / Outlook Calendar (read-only scope)
- Polls or subscribes (webhook/push notification where available) for new events matching sales-meeting heuristics (external attendee domain ≠ rep's company domain, event has ≥1 external guest, not an internal recurring standup)
- On match, emits a "brief requested" event ~30–45 minutes before meeting start, with attendee names/emails and company domain

**2. Data ingestion layer**
- Pulls public data only, per attendee/company:
  - **LinkedIn**: company page + attendee profile signals (role, tenure, recent posts) — subject to LinkedIn API/ToS constraints (see risks)
  - **Google News**: recent company mentions (funding, leadership changes, product launches)
  - **Crunchbase**: funding history, headcount, industry
  - **G2**: product reviews of the attendee's current tool stack, where inferable
- Normalizes all sources into a single structured "account context" object with source URL + retrieval timestamp attached to every field (required for the citation/freshness safeguards below)

**3. AI brief engine**
- Retrieval-Augmented Generation (RAG) over **two separate indices**: (a) external account-intelligence index built from the data ingestion layer, and (b) internal product-knowledge index — one-pagers, battlecards, case studies uploaded once by the admin (see Section 13). The LLM only writes claims it can ground in one of these two retrieved sources — it does not free-generate facts.
- Prompt explicitly requires every claim to carry a source; ungrounded claims are suppressed rather than shown
- Output: structured brief with sections — stakeholder card(s), account news, tech-stack signal, suggested talking points (the last of these draws on the internal index, not just prospect data)
- Also checks the account-memory store (Section 12) for any prior brief on this company/attendee and surfaces it as a delta
- Target latency: <90 seconds P95 (calendar detection → brief delivered)

**4. AI safeguards (attached to the brief engine, not a separate delivery step)**
- Source-citation requirement on every claim
- Confidence thresholds — low-confidence claims flagged "verify before use" instead of stated as fact
- Freshness timestamps on every data point shown to the rep
- Human-in-the-loop correction (rep can flag "was this accurate?" — feeds back as signal, does not require an edit UI in MVP)

**5. Delivery layer**
- Email (transactional) with subject line referencing the meeting, sent ~25–30 minutes before start
- One-click web view link — no login, session token in URL, expires after a set window
- (Slack delivery, CRM sidebar, and in-app notification are explicitly P1 — not built here)

**6. Analytics & metrics**
- Tracks: brief generated, brief opened, time-to-open relative to meeting start, calendar integration completion, time-to-first-brief
- Feeds the North Star Metric directly (see Section 8)

### 6.2 Data flow (text version of the diagram)
`Calendar trigger → Data ingestion (LinkedIn/News/Crunchbase/G2) → AI brief engine (RAG) ⇄ AI safeguards → Delivery (email + web view) → Analytics (Brief CTR)`

### 6.3 Suggested tech stack (indicative, for demo purposes)
- **Backend**: Node.js or Python (FastAPI) service orchestrating the pipeline
- **LLM**: Claude or GPT-4-class model via API, with RAG over ingested source documents
- **Calendar**: Google Calendar API + Microsoft Graph API (OAuth2)
- **Data ingestion**: scheduled jobs / on-demand fetch per triggered meeting, cached per company for 7 days (staleness re-enrichment)
- **Storage**: Postgres for structured account/brief records; a vector store (e.g. pgvector) for retrieved source chunks
- **Email**: SendGrid or Amazon SES
- **Web view**: lightweight server-rendered page, tokenized URL, no auth wall
- **Observability**: latency + hallucination-rate dashboards (Datadog/New Relic class tooling)

---

## 7. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | System shall detect a new calendar event with ≥1 external attendee and classify it as a sales meeting | P0 |
| FR-2 | System shall generate a brief containing stakeholder card(s), account news, and talking points using only public data | P0 |
| FR-3 | Every factual claim in a brief shall carry an inline source citation | P0 |
| FR-4 | System shall deliver the brief via email 25–30 minutes before meeting start | P0 |
| FR-5 | Email shall contain a one-click web view link requiring no additional login | P0 |
| FR-6 | System shall log brief-generated and brief-opened events with timestamps | P0 |
| FR-7 | System shall flag low-confidence claims visually rather than presenting them as fact | P0 |
| FR-8 | Rep shall be able to submit a single thumbs up/down on brief accuracy | P1 (nice-to-have for demo, not blocking) |

## 8. Non-functional requirements

| Category | Requirement |
|---|---|
| Latency | Brief generation <90 seconds P95, calendar-detect to delivery |
| Accuracy | ≥90% of factual claims verifiably correct (spot-check audit) |
| Hallucination rate | <5% of briefs contain any unverifiable/fabricated claim |
| Source coverage | ≥85% of claims carry an inline citation |
| Privacy | Only public data sources in MVP; no CRM or private data ingestion; GDPR-aware handling of any EU attendee data |
| Reliability | Calendar integration completion >80% in first session (i.e., OAuth flow must be low-friction) |

## 9. North Star metric & supporting metrics (MVP window: Day 0–60)

**North Star: Brief Click-Through Rate** = briefs opened before the meeting ÷ total briefs generated. **Target: ≥65% by Day 60.**

Supporting metrics for the demo:
- Calendar Integration Completion — target >80% within first session
- Time to First Brief (TTFB) — target <2 hours from signup
- Brief Accuracy Rate — target >90%
- Hallucination Rate — target <5%
- Rep Trust Score (1–5 self-report) — target >4.0

## 10. Risks specific to the MVP build

| Risk | Mitigation for MVP |
|---|---|
| LinkedIn API/ToS restrictions limit attendee-level data | Fall back to publicly available company-level signals + attendee's public posts only where permitted; do not scrape private profile data |
| LLM hallucinates a stakeholder fact, rep is embarrassed on a call | RAG grounding + mandatory citations + confidence flags (Section 6.1.4) |
| Reps never connect their calendar (biggest single point of failure) | Make OAuth the only setup step; no other config required before first brief |
| Public-data-only briefs feel thin compared to future CRM-enriched version | Frame explicitly in demo as "Day 0 public-data MVP" — CRM/Slack are the proven-if-hypothesis-holds Phase 1 build |

## 11. Calendar data requirements & meeting classification

The MVP cannot assume calendar invites arrive "clean." A trigger built on external-domain-detection alone will misfire on recruiter calls, internal meetings, and generic aliases (`sales@`, `info@`).

**Classification approach — confidence-scored, not binary:**

| Signal | Weight |
|---|---|
| ≥1 attendee domain ≠ rep's company domain | Strong positive |
| Attendee count between 1–4 | Positive |
| Title/description contains keywords ("demo", "discovery", "intro call", "renewal", "QBR") | Positive |
| One-off event, not a recurring series | Positive |
| Attendee email is a generic alias (`info@`, `sales@`, `noreply@`) | Negative |
| Internal-only domain match | Strong negative |

**Rule:** above a confidence threshold, auto-generate the brief silently (this is the zero-effort path Rohan needs). Below threshold, do **not** guess — send a single-tap prompt in the calendar reminder itself: *"Is this a sales meeting? Yes / No."* Every response is training signal, improving the classifier for every future rep without requiring the rep to manually tag anything up front.

**What we explicitly do not ask reps to do:** create calendar categories, use special naming conventions, or fill in a form before a brief can be generated. Any requirement like that violates the "zero rep effort" hypothesis this MVP exists to test.

## 12. Cross-meeting account memory (without a CRM)

Since CRM integration is P1, not P0, the MVP has no external system of record for "what happened last time." Building that memory has to happen inside SalesIntel itself:

- Every generated brief is stored as a structured record: company, stakeholders, signals surfaced, and date.
- When the same company or attendee reappears on a future calendar event, the new brief is generated as a **delta**: "Last briefed 12 days ago — here's what's changed since," rather than resetting to zero.
- This gives the rep organizational memory (the exact gap the Phase 1 report names as Layer 2) without requiring any CRM write access.

**What this cannot capture:** what was actually discussed, promised, or objected to on the call — that requires either rep input or conversation intelligence, both out of scope for MVP. To bridge this gap cheaply, the one-click web view includes a single **optional** free-text field — *"Anything worth remembering for next time?"* — logged against the account record. This is the minimum viable seed of organizational memory, and it's the natural on-ramp to the Phase 1 CRM-enriched version.

## 13. Seeding the AI with proprietary product knowledge

Public sources (LinkedIn, news, Crunchbase, G2) describe the **prospect** — they say nothing about **our own product**. Without a separate source of truth for positioning, the "talking points" section of the brief would either be generic or, worse, hallucinated. This has to be solved architecturally, not left implicit:

- **A second, separate knowledge index — distinct from the external account-intelligence index used for prospect research.** This one holds proprietary, first-party content: a product one-pager, competitive battlecards, pricing tiers, and 2–3 case studies.
- **Owner:** consistent with the Priya (RevOps admin) persona already defined in Phase 1 — she is the one who configures things once for the whole team. In MVP terms, this is a single lightweight upload step during onboarding, not a full CRM integration.
- **At generation time**, the brief engine retrieves from *both* indices and combines them: external signal (what's happening at the prospect) + internal knowledge (what we sell and how we're differentiated) → an actual talking point, rather than a restated fact about the prospect.

This addition changes Section 6.1's "AI brief engine" component: it now retrieves from two RAG sources, not one, and the onboarding flow requires one small admin-side setup step (product knowledge upload) even though the MVP otherwise has zero CRM dependency.

## 14. Demo narrative (suggested flow for the presentation)

1. Show the problem: the 7-tab manual workflow (from Phase 1 signal data)
2. Show a rep connecting their calendar (OAuth) — this is the *only* setup step
3. Show a real meeting appearing in the pipeline and a brief being generated end-to-end
4. Show the brief itself: stakeholder card, account news, talking points — each claim with a citation
5. Show the email + one-click web view (no login)
6. Close on the metric that matters: Brief Click-Through Rate, and why everything downstream (CRM, Slack, revenue impact) is gated on this one number first

---

*Prepared by Team COSMOS, based on the Phase 1 Product Strategy & Opportunity Assessment (April 2025).*
