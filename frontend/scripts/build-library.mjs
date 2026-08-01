// Build the in-app Developer Library served at /library/*.
// - Copies the two self-contained HTML docs as-is.
// - Renders the Markdown docs (Runbook, Build Plan) to styled, theme-aware HTML.
// - Emits an index page linking all of them with friendly names.
// Runs as part of `npm run build` (and standalone via `npm run library`). Output
// lands in frontend/public/library/, which Vite copies to dist/ and Caddy serves.
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { marked } from "marked";

const here = dirname(fileURLToPath(import.meta.url));
const FRONTEND = resolve(here, "..");
const DOCS = resolve(FRONTEND, "..", "docs");
const OUT = resolve(FRONTEND, "public", "library");
mkdirSync(OUT, { recursive: true });

marked.setOptions({ gfm: true, breaks: false });

// Friendly catalog — order + names shown on the index and in the Settings card.
const DOCS_LIST = [
  { file: "how-it-works.html", title: "How It Works",
    blurb: "A plain-English tour of the technology and how a briefing is built." },
  { file: "project-tracker.html", title: "Build Tracker",
    blurb: "Every feature we've shipped, grouped by phase." },
  { file: "runbook.html", title: "Operations Runbook",
    blurb: "Setup, running, deployment, and troubleshooting." },
  { file: "build-plan.html", title: "Architecture & Build Plan",
    blurb: "The design, tech stack, and product roadmap." },
];

function page(title, bodyHtml, { back = true } = {}) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} — SalesIntel AI</title>
<style>
  :root{ --bg:#f6f7fb; --surface:#fff; --line:#e1e4ef; --ink:#191c2e; --ink-2:#4b5069; --ink-3:#767c96; --accent:#4b4ee6; --accent-2:#3a3cc0; --code-bg:#eef0f7; }
  @media (prefers-color-scheme:dark){ :root{ --bg:#0e1020; --surface:#171a2e; --line:#2c3152; --ink:#e9ebf6; --ink-2:#aab0cb; --ink-3:#7b8199; --accent:#8f92f6; --accent-2:#adaeff; --code-bg:#1f2339; } }
  *{box-sizing:border-box} html{scroll-behavior:smooth}
  body{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; -webkit-font-smoothing:antialiased; }
  .bar{ position:sticky; top:0; z-index:5; display:flex; align-items:center; gap:12px; padding:12px 20px; background:color-mix(in srgb,var(--surface) 88%,transparent); backdrop-filter:blur(8px); border-bottom:1px solid var(--line); }
  .bar a{ color:var(--accent-2); text-decoration:none; font-weight:600; font-size:14px; }
  .bar .sep{ color:var(--ink-3); } .bar .cur{ color:var(--ink-3); font-size:14px; }
  main{ max-width:860px; margin:0 auto; padding:34px 22px 90px; }
  h1,h2,h3,h4{ line-height:1.25; margin:1.6em 0 .5em; }
  h1{ font-size:1.9rem; margin-top:.2em; } h2{ font-size:1.4rem; border-bottom:1px solid var(--line); padding-bottom:.3em; } h3{ font-size:1.15rem; }
  p,li{ color:var(--ink-2); } a{ color:var(--accent-2); }
  code{ font-family:ui-monospace,"Cascadia Code",Consolas,monospace; font-size:.87em; background:var(--code-bg); border:1px solid var(--line); border-radius:5px; padding:.1em .4em; color:var(--accent-2); }
  pre{ background:var(--code-bg); border:1px solid var(--line); border-radius:10px; padding:14px 16px; overflow-x:auto; } pre code{ background:none; border:0; padding:0; color:var(--ink); }
  table{ border-collapse:collapse; width:100%; display:block; overflow-x:auto; margin:1em 0; font-size:.93em; }
  th,td{ border:1px solid var(--line); padding:8px 11px; text-align:left; } th{ background:var(--code-bg); }
  blockquote{ margin:1em 0; padding:.4em 1em; border-left:3px solid var(--accent); background:var(--code-bg); border-radius:0 8px 8px 0; }
  hr{ border:0; border-top:1px solid var(--line); margin:2em 0; }
  img{ max-width:100%; }
  .cards{ display:grid; gap:12px; grid-template-columns:1fr 1fr; margin-top:8px; }
  @media (max-width:640px){ .cards{ grid-template-columns:1fr; } }
  .lib{ display:block; text-decoration:none; background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:18px 20px; transition:border-color .15s, transform .15s; }
  .lib:hover{ border-color:var(--accent); transform:translateY(-1px); }
  .lib h3{ margin:0 0 4px; font-size:1.05rem; color:var(--ink); } .lib p{ margin:0; font-size:.9rem; color:var(--ink-3); }
  .lede{ color:var(--ink-2); font-size:1.05rem; }
</style>
</head>
<body>
  <div class="bar">
    <a href="/settings">&larr; Back to app</a>
    ${back ? '<span class="sep">/</span><a href="/library/">Developer Library</a>' : ""}
    <span class="sep">/</span><span class="cur">${title}</span>
  </div>
  <main>${bodyHtml}</main>
</body>
</html>`;
}

// Render the two Markdown docs.
function renderMd(src, dest, title) {
  const md = readFileSync(resolve(DOCS, src), "utf8");
  writeFileSync(resolve(OUT, dest), page(title, marked.parse(md)));
}
renderMd("RUNBOOK.md", "runbook.html", "Operations Runbook");
renderMd("BUILD_PLAN.md", "build-plan.html", "Architecture & Build Plan");

// Copy the two self-contained HTML docs verbatim (they carry their own styles).
copyFileSync(resolve(DOCS, "HOW_IT_WORKS.html"), resolve(OUT, "how-it-works.html"));
copyFileSync(resolve(DOCS, "PROJECT_TRACKER.html"), resolve(OUT, "project-tracker.html"));

// Index page.
const cards = DOCS_LIST.map(
  (d) => `<a class="lib" href="/library/${d.file}"><h3>${d.title}</h3><p>${d.blurb}</p></a>`,
).join("\n");
const indexBody = `<h1>Developer Library</h1>
<p class="lede">Guides and reference for how SalesIntel AI works — the technology, what's shipped, and how it's run and deployed.</p>
<div class="cards">${cards}</div>`;
writeFileSync(resolve(OUT, "index.html"), page("Developer Library", indexBody, { back: false }));

console.log(`[library] built ${DOCS_LIST.length} docs + index -> ${OUT}`);
