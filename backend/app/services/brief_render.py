"""Render BriefContent -> polished, self-contained HTML (AI-Engine Agent, S4.3).

The output is a single HTML string with inline CSS (light theme), suitable for the
brief view and client-side PDF export. Includes a lightweight markdown converter
(bold, italics, inline code, bullet/numbered lists, headings, paragraphs) plus
[S#] citation chips and a linked Sources list.
"""
from __future__ import annotations

import html
import re
from typing import List

from app.schemas import (
    PERSONA_LABELS,
    PERSONA_TAGLINES,
    BriefContent,
    BriefSection,
    BriefSource,
    Confidence,
)

_LOW_FLAG = "verify before use"


# --------------------------------------------------------------------------- #
# Markdown -> HTML (small, dependency-free)
# --------------------------------------------------------------------------- #
def _inline_md(text: str) -> str:
    """Convert inline markdown on an ALREADY html-escaped string."""
    # Bold: **x** or __x__
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # Italic: *x* or _x_ (avoid touching bold already handled)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"<em>\1</em>", text)
    # Inline code: `x`
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    # Markdown links: [label](url)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    # Citation chips: [S1], [S2] (leave links above intact — these are bare)
    text = re.sub(
        r"\[(S\d+)\]",
        r'<span class="cite">\1</span>',
        text,
    )
    return text


def _md_to_html(md: str) -> str:
    """Block-level markdown: headings, ul/ol lists, paragraphs."""
    if not md:
        return ""
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    list_type: str | None = None  # "ul" | "ol"

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            close_list()
            continue

        # Headings (### etc.)
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_list()
            level = min(len(m.group(1)) + 2, 6)  # shift down so section h2 stays top
            out.append(f"<h{level}>{_inline_md(html.escape(m.group(2)))}</h{level}>")
            continue

        # Unordered list item
        m = re.match(r"^[-*+]\s+(.*)$", stripped)
        if m:
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            out.append(f"<li>{_inline_md(html.escape(m.group(1)))}</li>")
            continue

        # Ordered list item
        m = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if m:
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append(f"<li>{_inline_md(html.escape(m.group(1)))}</li>")
            continue

        # Paragraph
        close_list()
        out.append(f"<p>{_inline_md(html.escape(stripped))}</p>")

    close_list()
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Section + sources rendering
# --------------------------------------------------------------------------- #
def _is_low(section: BriefSection) -> bool:
    if section.confidence == Confidence.low:
        return True
    return any(_LOW_FLAG in (f or "").lower() for f in section.flags)


def _confidence_label(section: BriefSection) -> str:
    return {
        Confidence.high: "High confidence",
        Confidence.medium: "Medium confidence",
        Confidence.low: "Low confidence",
    }.get(section.confidence, "Medium confidence")


def _render_section(index: int, section: BriefSection) -> str:
    low = _is_low(section)
    badge = (
        '<span class="badge badge-verify">Verify before use</span>' if low else ""
    )
    conf_class = f"conf conf-{section.confidence.value}"
    conf = f'<span class="{conf_class}">{html.escape(_confidence_label(section))}</span>'

    # Extra flags (other than the low-confidence marker) shown as chips.
    extra_flags = [
        f for f in section.flags if _LOW_FLAG not in (f or "").lower() and f.strip()
    ]
    flags_html = ""
    if extra_flags:
        chips = "".join(
            f'<span class="flag">{html.escape(f)}</span>' for f in extra_flags
        )
        flags_html = f'<div class="flags">{chips}</div>'

    body = _md_to_html(section.content_md)
    return f"""
    <section class="brief-section{' low' if low else ''}">
      <div class="sec-head">
        <h2><span class="sec-num">{index}</span>{html.escape(section.title)}</h2>
        <div class="sec-meta">{conf}{badge}</div>
      </div>
      {flags_html}
      <div class="sec-body">{body}</div>
    </section>"""


def _render_sources(sources: List[BriefSource]) -> str:
    if not sources:
        return ""
    items = []
    for s in sources:
        title = html.escape(s.title or s.marker)
        meta_bits = []
        if s.filename:
            meta_bits.append(html.escape(s.filename))
        meta = f' <span class="src-file">{" · ".join(meta_bits)}</span>' if meta_bits else ""
        if s.url:
            title = f'<a href="{html.escape(s.url)}">{title}</a>'
        items.append(
            f'<li><span class="src-marker">{html.escape(s.marker)}</span>'
            f'<span class="src-title">{title}{meta}</span></li>'
        )
    return f"""
    <section class="sources">
      <h2>Sources</h2>
      <ol class="source-list">
        {''.join(items)}
      </ol>
    </section>"""


_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #f4f6f9;
  color: #1f2933;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  font-size: 15px;
}
.wrap { max-width: 860px; margin: 0 auto; padding: 40px 32px 64px; }
.doc {
  background: #ffffff;
  border: 1px solid #e3e8ef;
  border-radius: 14px;
  padding: 40px 44px;
  box-shadow: 0 1px 3px rgba(16,24,40,0.06), 0 6px 24px rgba(16,24,40,0.05);
}
.kicker {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 11px;
  font-weight: 700;
  color: #c2410c;
  margin-bottom: 10px;
}
h1 {
  font-size: 26px;
  line-height: 1.25;
  margin: 0 0 6px;
  color: #0f172a;
  font-weight: 700;
}
.headline {
  font-size: 16px;
  color: #475569;
  margin: 4px 0 8px;
  font-weight: 500;
}
.meta-row {
  font-size: 12.5px;
  color: #64748b;
  border-top: 1px solid #eef1f5;
  border-bottom: 1px solid #eef1f5;
  padding: 10px 0;
  margin: 18px 0 8px;
}
.brief-section {
  padding: 24px 0 6px;
  border-top: 1px solid #eef1f5;
}
.brief-section:first-of-type { border-top: none; }
.brief-section.low { position: relative; }
.sec-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
h2 {
  font-size: 18px;
  margin: 0;
  color: #0f172a;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}
.sec-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px; height: 26px;
  border-radius: 7px;
  background: #f97316;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  flex: 0 0 auto;
}
.sec-meta { display: flex; align-items: center; gap: 8px; }
.conf {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 999px;
  white-space: nowrap;
}
.conf-high { background: #dcfce7; color: #166534; }
.conf-medium { background: #fef9c3; color: #854d0e; }
.conf-low { background: #fee2e2; color: #991b1b; }
.badge-verify {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 999px;
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  white-space: nowrap;
}
.flags { margin: 8px 0 0 36px; }
.flag {
  display: inline-block;
  font-size: 11px;
  color: #7c2d12;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 6px;
  padding: 2px 8px;
  margin: 2px 6px 2px 0;
}
.sec-body { margin: 10px 0 0 36px; }
.sec-body p { margin: 0 0 12px; }
.sec-body ul, .sec-body ol { margin: 0 0 12px; padding-left: 22px; }
.sec-body li { margin: 4px 0; }
.sec-body h4, .sec-body h5, .sec-body h6 {
  margin: 14px 0 6px; font-size: 14px; color: #334155;
}
.sec-body code {
  background: #f1f5f9;
  border-radius: 4px;
  padding: 1px 5px;
  font-family: "SF Mono", Menlo, Consolas, monospace;
  font-size: 12.5px;
}
.cite {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 5px;
  padding: 0 5px;
  margin: 0 1px;
  vertical-align: baseline;
  line-height: 1.5;
}
a { color: #1d4ed8; text-decoration: none; }
a:hover { text-decoration: underline; }
.sources {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 2px solid #eef1f5;
}
.source-list { list-style: none; padding: 0; margin: 8px 0 0; }
.source-list li {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13.5px;
}
.src-marker {
  flex: 0 0 auto;
  font-weight: 700;
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 5px;
  padding: 1px 8px;
  height: fit-content;
}
.src-file { color: #94a3b8; font-size: 12px; }
.footer {
  margin-top: 24px;
  font-size: 11.5px;
  color: #94a3b8;
  text-align: center;
}
@media print {
  body { background: #fff; }
  .wrap { padding: 0; max-width: none; }
  .doc { border: none; box-shadow: none; border-radius: 0; padding: 0; }
  .brief-section { page-break-inside: avoid; }
}
"""


def render_html(brief: BriefContent) -> str:
    """Render a BriefContent into a polished, self-contained HTML document."""
    company = html.escape(brief.company or brief.company_slug or "Prospect")
    headline = html.escape(brief.headline or "")
    generated = ""
    if brief.generated_at:
        generated = brief.generated_at.strftime("%B %d, %Y %H:%M UTC")

    sections_html = "\n".join(
        _render_section(i, sec) for i, sec in enumerate(brief.sections, start=1)
    )
    sources_html = _render_sources(brief.sources)

    pv = getattr(brief.persona, "value", str(brief.persona))
    persona_label = PERSONA_LABELS.get(pv, "Sales Representative")
    persona_tagline = PERSONA_TAGLINES.get(pv, "")

    headline_html = f'<p class="headline">{headline}</p>' if headline else ""
    meta_html = (
        f'<div class="meta-row">{html.escape(persona_label)} view'
        + (f' · {html.escape(persona_tagline)}' if persona_tagline else "")
        + (f' · Generated {html.escape(generated)}' if generated else "")
        + "</div>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{company} — Pre-Sales Brief</title>
<style>{_CSS}</style>
</head>
<body>
  <div class="wrap">
    <div class="doc">
      <div class="kicker">{html.escape(persona_label)} · Pre-Sales Brief</div>
      <h1>{company}</h1>
      {headline_html}
      {meta_html}
      {sections_html}
      {sources_html}
      <div class="footer">
        Grounded in the cited sources. Claims marked &ldquo;Verify before use&rdquo; are
        low-confidence and should be confirmed independently.
      </div>
    </div>
  </div>
</body>
</html>"""
