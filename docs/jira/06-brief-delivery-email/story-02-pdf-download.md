# SI-6.2 — Client-side PDF / HTML download

| Field | Value |
|---|---|
| Issue type | Story |
| Parent epic | SI-6 — Brief Delivery: Web View & Email |
| Status | Done |
| Priority | Medium |
| Story points | 3 |
| Component | Delivery |
| Labels | frontend |

## User story
As a sales rep, I want to download the brief as a PDF from the browser, so that I can take it into a meeting, share it, or file it without needing the app open.

## Description
This story lets the rep save the on-screen brief as a portable file directly from the browser. Downloading is deliberately **client-side**: it runs html2pdf.js over the brief HTML that is already rendered in the viewer, producing a clean A4 portrait PDF. Because the conversion happens entirely in the browser, the backend needs **no PDF libraries, no headless browser, and no rendering service** — a conscious POC choice that keeps the server dependency-free and deployment simple.

The export is tuned for a faithful, readable document: A4 portrait, sensible page margins, a white background, and a higher canvas scale so text and the KPI strip stay crisp. The output filename is derived from the brief and the active persona and passed through a filename-sanitizer so it is always a safe, predictable name on disk.

Because the source of truth is the same server-rendered brief HTML shown on screen, the PDF matches what the rep sees — the nine sections, citations, KPI strip, and confidence indicators — with no separate "print template" to drift out of sync.

## Acceptance criteria
```gherkin
Scenario: Download the viewed brief as PDF
  Given the rep is viewing a ready brief
  When the rep triggers Download
  Then an A4 portrait PDF of the rendered brief is generated in the browser
  And it is saved with a persona-specific, sanitized filename
```

```gherkin
Scenario: No server PDF dependency is used
  Given the download runs
  When the PDF is produced
  Then it is produced entirely client-side via html2pdf.js over the rendered HTML
  And no server-side PDF endpoint or dependency is invoked
```

```gherkin
Scenario: Unsafe characters in the brief name (edge case)
  Given a brief whose name contains spaces or special characters
  When the file is downloaded
  Then the filename is sanitized to safe characters before saving
```

## Technical notes (reference)
- Key files: `frontend/src/lib/pdf.ts`, `frontend/src/pages/BriefView.tsx`.
- `downloadElementAsPdf(element, filename)` calls html2pdf.js with `format: "a4"`, `orientation: "portrait"`, 12mm margins, `html2canvas` `scale: 2` and white background; `safeFilename(name)` strips non-`[\w.-]` characters and caps length.
- POC shortcut: intentionally no server-side PDF generation — the client renders the already-produced brief HTML, keeping the backend free of PDF deps.

## Definition of Done
- [x] A Download action on the brief view produces an A4 portrait PDF of the rendered brief.
- [x] Conversion is fully client-side (html2pdf.js) with no server PDF dependency.
- [x] Output filename includes the active persona and is sanitized.
- [x] The PDF reflects the same sections/citations/KPI strip shown on screen.
