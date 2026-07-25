# SI-6.4 — Persona-tailored email composition + brief attachment

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-6 — Brief Delivery: Web View & Email |
| Status | Done |
| Priority | High |
| Story points | 5 |
| Component | Delivery |
| Labels | backend, ai |

## User story
As a sales rep, I want the emailed brief to lead with the two sections that matter most for my role and carry the full brief as an attachment, so that the recipient gets an instantly useful digest without losing any detail.

## Description
This story implements "Format C" — the actual composition and delivery logic behind "Send as email." The email **body** is a persona-tailored HTML digest that differs per role: an **AE** digest headlines the recommended angle and stakeholders, an **SDR** digest headlines the outreach opener and target contact, and an **SE** digest headlines the demo focus and technical objections. The digest is inline-styled HTML (so it survives email clients), leads with the company, headline, persona label/tagline, and a compact facts row drawn from the brief's `key_facts`, then renders the two role-specific sections. A plain-text alternative is generated alongside for non-HTML clients. If a persona's expected sections are missing, composition defensively falls back to the brief's first two sections so a digest is always produced.

The **full brief** is attached as a **PDF** (`application/pdf`), rendered server-side from a print-friendly layout so it previews as a document in the recipient's mail client — earlier the brief shipped as a `.html` file, which some clients previewed as raw HTML source rather than a readable page. The PDF is produced with **xhtml2pdf**, a pure-Python renderer with no GTK / wkhtmltopdf / system dependencies (honoring the project's "no server PDF deps" constraint). It is named from the company and persona (`"<company>-<persona>-brief.pdf"`) and run through a filename sanitizer. Rendering is **fail-soft**: if PDF generation ever errors, composition falls back to the self-contained `.html` attachment so the email still sends. So the recipient gets a scannable digest in the body plus the complete brief as a document-previewable attachment.

**Delivery** mirrors the LLM mock pattern. `send_brief_email` sends for real — via the Python standard library `smtplib` + `email.message.EmailMessage` with STARTTLS, a plain-text body, an HTML alternative, and the PDF attachment (both the Gmail and SMTP send paths attach using the attachment's own content-type, `application/pdf`) — only when SMTP is configured **and** `mock_email` is off. Otherwise it returns a `demo` result: the email is fully composed but nothing leaves the machine. The send path is **exception-safe**: an empty recipient returns an `error` result, and any SMTP failure is caught and surfaced as a UI-friendly `error` message rather than raising — so the API request can never crash on a mail problem. No third-party mail dependency is introduced.

## Acceptance criteria
```gherkin
Scenario: AE digest headlines the right sections
  Given a ready brief for the AE persona
  When the email is composed
  Then the digest body leads with the recommended angle and stakeholders
  And the full brief is attached as a PDF (application/pdf) whose bytes begin with the %PDF- header
```

```gherkin
Scenario: PDF rendering fails, email still sends (edge case)
  Given PDF generation of the attachment raises
  When the email is composed
  Then composition falls back to the self-contained .html attachment
  And the email is still produced and sent
```

```gherkin
Scenario: SDR and SE digests are role-specific
  Given a ready brief
  When it is composed for the SDR persona then the SE persona
  Then the SDR digest leads with the outreach opener and target contact
  And the SE digest leads with the demo focus and technical objections
```

```gherkin
Scenario: Demo send when SMTP is not configured
  Given SMTP is not configured or mock_email is on
  When send_brief_email runs with a valid recipient
  Then it returns mode "demo" with delivered false and nothing is sent
```

```gherkin
Scenario: SMTP failure never crashes the request (edge case)
  Given SMTP is configured and mock_email is off
  When the SMTP server raises during send
  Then the exception is caught
  And an EmailSendResult with mode "error" and a friendly message is returned
```

## Technical notes (reference)
- Key files: `backend/app/services/email_service.py`, `backend/app/services/brief_render.py`, `backend/app/schemas.py`.
- `_DIGEST_SECTION_IDS` maps persona → two section ids (`ae`→recommended_angle/stakeholders, `sdr`→outreach_opener/target_contact, `se`→demo_focus/technical_objections); `_highlight_sections` falls back to the first two sections when ids are missing.
- `compose_brief_email` returns a `ComposedEmail` (subject, `body_html`, `plain_text`, attachment filename + bytes + content-type); the attachment is a PDF rendered by xhtml2pdf from the print-friendly layout over `render_html(brief)`, named `"<company>-<persona>-brief.pdf"` with `application/pdf`. If PDF rendering raises it falls back to the `.html` attachment (`text/html`).
- `send_brief_email` uses stdlib `smtplib` + `EmailMessage` with STARTTLS; both the Gmail and SMTP send paths attach using the attachment's declared content-type (maintype/subtype from `application/pdf`); `should_send = email_configured and not mock_email`; empty recipient and any exception both return `mode="error"` without raising.
- Dependency added: `xhtml2pdf==0.2.17` (pure-Python; no GTK / wkhtmltopdf / system deps) — not a mail dependency.
- POC shortcut: plain SMTP only (new-Outlook-only machine, no COM); demo-send is the default.

## Definition of Done
- [x] Persona-tailored HTML digest body composed for AE / SDR / SE with the correct headline sections.
- [x] Plain-text alternative generated; full brief attached as a PDF (`application/pdf`, `"<company>-<persona>-brief.pdf"`) rendered server-side with xhtml2pdf.
- [x] PDF rendering is fail-soft — falls back to the self-contained `.html` attachment if it errors, so the email still sends.
- [x] Both the Gmail and SMTP send paths attach using the attachment's content-type (`application/pdf`).
- [x] Real send via stdlib `smtplib`/`email.message` only when configured and not mocked; else demo-send.
- [x] Empty recipient and SMTP failures return an `error` result without raising.
- [x] No third-party mail dependency added (`xhtml2pdf` is a pure-Python PDF renderer, not a mail dependency).
