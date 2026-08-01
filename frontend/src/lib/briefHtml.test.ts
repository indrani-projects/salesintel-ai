import { describe, expect, it } from "vitest";
import type { BriefContent } from "../api/types";
import { escHtml, renderBriefToHtml } from "./briefHtml";

describe("escHtml", () => {
  it("escapes the HTML-significant characters", () => {
    expect(escHtml(`<img src=x onerror=alert(1)>`)).toBe(
      "&lt;img src=x onerror=alert(1)&gt;",
    );
    expect(escHtml(`a & b "c" 'd'`)).toBe("a &amp; b &quot;c&quot; &#39;d&#39;");
  });
});

describe("renderBriefToHtml XSS safety", () => {
  const XSS = `<img src=x onerror=alert(1)>`;

  const brief = {
    company: XSS,
    company_slug: "evil",
    persona: "sales_rep",
    headline: XSS,
    key_facts: [],
    sections: [{ title: XSS, content_md: "safe body", confidence: "high" }],
    sources: [{ marker: "S1", title: XSS, filename: XSS }],
    generated_at: null,
  } as unknown as BriefContent;

  it("never emits a raw <img ... onerror> from any interpolated field", () => {
    const html = renderBriefToHtml(brief);
    // The dangerous raw tag must not appear anywhere in the output…
    expect(html).not.toContain("<img src=x onerror");
    // …and every injection point must be escaped instead.
    expect(html).toContain("&lt;img src=x onerror=alert(1)&gt;");
  });

  it("still renders legitimate content unchanged", () => {
    const ok = {
      ...brief,
      company: "The Sleep Company",
      headline: "Series C omnichannel retailer",
      sections: [{ title: "Snapshot", content_md: "**Bold** fact", confidence: "high" }],
      sources: [{ marker: "S1", title: "Annual report", filename: "report.pdf" }],
    } as unknown as BriefContent;
    const html = renderBriefToHtml(ok);
    expect(html).toContain("The Sleep Company");
    expect(html).toContain("Series C omnichannel retailer");
    expect(html).toContain("<strong>Bold</strong>");
    expect(html).toContain("report.pdf");
  });
});
