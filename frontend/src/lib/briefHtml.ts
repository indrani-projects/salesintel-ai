import type { BriefContent } from "../api/types";

/** Minimal, dependency-free markdown → HTML for PDF export fallback. */
function mdToHtml(md: string): string {
  const esc = (s: string) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  const inline = (s: string) =>
    esc(s)
      .replace(/\[(S\d+)\]/g, '<sup style="color:#4f46e5;font-weight:600">[$1]</sup>')
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, '<code style="background:#f1f5f9;padding:1px 4px;border-radius:3px">$1</code>');

  const lines = md.split(/\r?\n/);
  const out: string[] = [];
  let inList = false;
  const closeList = () => {
    if (inList) {
      out.push("</ul>");
      inList = false;
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      closeList();
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.*)$/);
    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (bullet) {
      if (!inList) {
        out.push('<ul style="margin:6px 0 6px 18px;padding:0">');
        inList = true;
      }
      out.push(`<li style="margin:2px 0">${inline(bullet[1])}</li>`);
    } else if (heading) {
      closeList();
      out.push(
        `<h4 style="margin:10px 0 4px;font-size:14px;font-weight:600">${inline(heading[2])}</h4>`,
      );
    } else {
      closeList();
      out.push(`<p style="margin:6px 0;line-height:1.5">${inline(line)}</p>`);
    }
  }
  closeList();
  return out.join("");
}

/** Render a full brief to a styled, self-contained HTML string (used for PDF). */
export function renderBriefToHtml(content: BriefContent): string {
  const sections = content.sections
    .map((s) => {
      const lowConf = s.confidence === "low";
      const flag = lowConf
        ? '<span style="margin-left:8px;font-size:11px;color:#b45309;background:#fffbeb;border:1px solid #fde68a;border-radius:999px;padding:1px 8px">verify before use</span>'
        : "";
      return `
        <section style="margin:0 0 18px;padding:14px 16px;border:1px solid #e2e8f0;border-radius:12px">
          <h3 style="margin:0 0 6px;font-size:15px;font-weight:700;color:#0f172a">${s.title}${flag}</h3>
          <div style="font-size:13px;color:#334155">${mdToHtml(s.content_md)}</div>
        </section>`;
    })
    .join("");

  const sources = content.sources
    .map(
      (src) =>
        `<li style="margin:3px 0"><strong style="color:#4f46e5">[${src.marker}]</strong> ${src.title}${
          src.filename ? ` <span style="color:#94a3b8">— ${src.filename}</span>` : ""
        }</li>`,
    )
    .join("");

  return `
    <div style="font-family:Inter,system-ui,sans-serif;color:#0f172a;background:#fff">
      <div style="border-bottom:2px solid #4f46e5;padding-bottom:10px;margin-bottom:16px">
        <div style="font-size:12px;font-weight:700;letter-spacing:.08em;color:#4f46e5">SALESINTEL AI · PRE-CALL BRIEF</div>
        <h1 style="margin:6px 0 2px;font-size:22px;font-weight:800">${content.company}</h1>
        ${content.headline ? `<p style="margin:0;font-size:13px;color:#475569">${content.headline}</p>` : ""}
      </div>
      ${sections}
      <section style="margin-top:8px;padding:14px 16px;border:1px solid #e2e8f0;border-radius:12px;background:#f8fafc">
        <h3 style="margin:0 0 6px;font-size:14px;font-weight:700">Sources</h3>
        <ul style="margin:0;padding-left:18px;font-size:12px;color:#475569">${sources}</ul>
      </section>
    </div>`;
}
