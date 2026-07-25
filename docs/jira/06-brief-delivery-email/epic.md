# EPIC SI-6 — Brief Delivery: Web View & Email

| Field | Value |
|---|---|
| Issue type | Epic |
| Suggested key | SI-6 |
| Status | Done |
| Priority | High |
| Component | Delivery |
| Labels | frontend, backend, ux, api, ai |
| Story points (rollup) | 20 |

## Summary
Deliver the finished pre-sales brief to the rep three ways — an on-screen 9-section viewer, a client-side PDF/HTML download, and a persona-tailored "Send as email" flow.

## Description
Every earlier stage in SalesIntel AI exists to produce one artifact: a grounded, cited, 9-section pre-sales brief tailored to a persona (AE, SDR, or SE). This epic is the "last mile" — how that finished brief actually reaches the sales rep and leaves the app. It covers the three consumption surfaces a rep touches after a brief flips to `ready`: reading it in the browser, taking it offline as a file, and forwarding it to a colleague or to themselves as email.

The **on-screen viewer** (`BriefView.tsx`) is the primary surface. It renders all nine sections from the server-produced HTML/JSON, with a KPI strip built from `key_facts`, inline `[S#]` source citations, per-section confidence chips ("verify before use" on low-confidence claims), a persona toggle that re-fetches the brief for a different role, and the Scout Q&A panel. The **download** path is deliberately client-side: `lib/pdf.ts` runs html2pdf.js over the already-rendered brief HTML, so there are zero server-side PDF dependencies to install or maintain.

The **email** path is the richest piece. It implements "Format C": the email body is a persona-tailored HTML digest (AE gets recommended angle + stakeholders, SDR gets outreach opener + target contact, SE gets demo focus + technical objections), and the complete brief is attached as a **PDF** (`application/pdf`) that previews as a document in the recipient's mail client — it was previously a `.html` file, which some clients rendered as raw HTML source. The PDF is produced server-side with xhtml2pdf, a pure-Python renderer with no GTK / wkhtmltopdf / system dependencies, and rendering is fail-soft: if it errors, composition falls back to the self-contained `.html` attachment so the email still sends. Delivery mirrors the LLM mock pattern already used elsewhere in the codebase — a real email is sent only when SMTP is configured **and** `mock_email` is off; otherwise the app performs a "demo send" that composes and previews the message without anything leaving the machine. Real sending uses only the Python standard library (`smtplib` + `email.message`) — no third-party mail dependency — and the send path is exception-safe so it can never crash the request.

Because this is a POC, **demo-send is the intentional default**: the reviewer can exercise the whole compose/preview/confirm flow with no SMTP credentials configured. The target machine runs new Outlook only (no COM automation available), so plain SMTP is the only real-send transport supported by design.

## Stories in this epic
| Key | Story | Points | Priority |
|---|---|---|---|
| SI-6.1 | Brief viewer (9 sections, citations, confidence chips, KPI strip) | 5 | High |
| SI-6.2 | Client-side PDF / HTML download | 3 | Medium |
| SI-6.3 | Email settings & DTOs | 2 | Medium |
| SI-6.4 | Persona-tailored email composition + brief attachment | 5 | High |
| SI-6.5 | Email API & EmailDialog UI (preview + send/demo-send) | 5 | High |

## Epic acceptance criteria
```gherkin
Scenario: Rep reads a ready brief on screen
  Given a meeting whose brief status is "ready"
  When the rep opens the brief view
  Then all nine sections render with inline [S#] citations
  And a KPI strip shows the brief's key_facts
  And low-confidence sections display a "verify before use" chip
```

```gherkin
Scenario: Rep takes the brief offline
  Given the rep is viewing a ready brief
  When the rep clicks Download
  Then an A4 PDF of the rendered brief is generated in the browser
  And no server-side PDF dependency is invoked
```

```gherkin
Scenario: Rep sends the brief as email in demo mode
  Given SMTP is not configured on the backend
  When the rep opens "Send as email" and confirms
  Then the persona-tailored digest is composed and previewed with the full brief attached
  And the result reports a "demo" send with nothing delivered
```

## Out of scope
- Server-side PDF rendering or headless-browser export.
- Scheduled / recurring email digests or drip sequences.
- Outlook COM automation or any non-SMTP transport.
- Vector search or re-generation of brief content (owned by other epics).

## Dependencies
- Brief generation epic (produces the `ready` `BriefContent` this epic renders and sends).
- Shared contract files `schemas.py` / `frontend/src/api/types.ts` (DTO shapes consumed here).
