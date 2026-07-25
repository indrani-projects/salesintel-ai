import { useState } from "react";
import type { FormEvent } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Lock, Radar, Sparkles, User } from "lucide-react";
import {
  PERSONA_LABELS,
  PERSONA_ORDER,
  PERSONA_TAGLINES,
} from "../api/types";
import type { Persona } from "../api/types";
import { PERSONA_ACCENTS } from "../lib/persona";
import { setSessionPersona } from "../api/client";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [persona, setPersona] = useState<Persona>("sales_rep");
  const [submitting, setSubmitting] = useState(false);

  const accent = PERSONA_ACCENTS[persona];

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const who = name.trim() || "Guest";
    login({ name: who, persona });
    // Fresh session: drop any cached Scout chat so the cleared history shows immediately.
    queryClient.removeQueries({ queryKey: ["chat"] });
    // Fire-and-forget: record the active persona server-side (this also clears Scout
    // history on the backend) and kick off generation of its briefs. Never blocks entry.
    setSessionPersona(persona).catch(() => {
      /* best-effort */
    });
    navigate("/calendar", { replace: true });
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      {/* Brand panel */}
      <aside className="relative hidden overflow-hidden bg-nav p-12 text-white lg:flex lg:flex-col">
        {/* decorative gradient blobs */}
        <div className="pointer-events-none absolute -left-24 -top-24 h-80 w-80 rounded-full bg-brand-600/40 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 -right-16 h-96 w-96 rounded-full bg-[#6d70ff]/30 blur-3xl" />
        <div className="pointer-events-none absolute right-1/3 top-1/2 h-64 w-64 rounded-full bg-violet-500/20 blur-3xl" />

        <div className="relative flex items-center gap-2.5 font-bold tracking-tight">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-600 via-[#6d70ff] to-brand-600">
            <Radar className="h-5 w-5" />
          </span>
          <span className="text-lg">SalesIntel AI</span>
        </div>

        <div className="relative my-auto max-w-md">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-[12px] font-medium text-nav-ink">
            <Sparkles className="h-3.5 w-3.5" />
            Pre-meeting intelligence, on autopilot
          </div>
          <h1 className="text-[34px] font-extrabold leading-[1.1] tracking-tight">
            Walk into every meeting
            <br />
            already prepared.
          </h1>
          <p className="mt-4 max-w-sm text-[15px] leading-relaxed text-nav-ink">
            Grounded, cited pre-sales briefs — auto-generated from the open web and your
            Zoho catalog, tailored to your role.
          </p>

          <div className="mt-8 flex flex-wrap gap-2">
            {PERSONA_ORDER.map((p) => (
              <span
                key={p}
                className={`rounded-full border px-3 py-1 text-[12px] font-semibold ${
                  p === persona
                    ? "border-white/30 bg-white/15 text-white"
                    : "border-white/10 bg-white/[0.04] text-nav-ink"
                }`}
              >
                {PERSONA_LABELS[p]}
              </span>
            ))}
          </div>
        </div>

        <div className="relative text-[12px] text-nav-ink/70">
          Demo workspace · Zoho → prospect intelligence
        </div>
      </aside>

      {/* Form panel */}
      <main className="flex items-center justify-center bg-bg px-6 py-12">
        <div className="w-full max-w-sm">
          {/* compact logo on small screens */}
          <div className="mb-8 flex items-center gap-2.5 font-bold tracking-tight text-ink-900 lg:hidden">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-600 via-[#6d70ff] to-brand-600 text-white">
              <Radar className="h-5 w-5" />
            </span>
            <span className="text-lg">SalesIntel AI</span>
          </div>

          <h2 className="text-[26px] font-bold tracking-tight text-ink-900">Sign in</h2>
          <p className="mt-1 text-[14px] text-muted">
            Enter your name and choose the persona you'll work as.
          </p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-[13px] font-semibold text-ink-800">Name</span>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-muted" />
                <input
                  id="login-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Rohan M."
                  autoFocus
                  className="w-full rounded-xl border border-line bg-white py-2.5 pl-10 pr-3 text-[14px] outline-none transition focus:border-brand-600 focus:ring-2 focus:ring-brand-600/20"
                />
              </div>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-[13px] font-semibold text-ink-800">Password</span>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-muted" />
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Anything works (demo)"
                  className="w-full rounded-xl border border-line bg-white py-2.5 pl-10 pr-3 text-[14px] outline-none transition focus:border-brand-600 focus:ring-2 focus:ring-brand-600/20"
                />
              </div>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-[13px] font-semibold text-ink-800">
                Work as persona
              </span>
              <div className="relative">
                <span
                  className={`pointer-events-none absolute left-3 top-1/2 h-2.5 w-2.5 -translate-y-1/2 rounded-full ${accent.dot}`}
                />
                <select
                  id="login-persona"
                  value={persona}
                  onChange={(e) => setPersona(e.target.value as Persona)}
                  className="w-full appearance-none rounded-xl border border-line bg-white py-2.5 pl-9 pr-9 text-[14px] font-medium text-ink-900 outline-none transition focus:border-brand-600 focus:ring-2 focus:ring-brand-600/20"
                >
                  {PERSONA_ORDER.map((p) => (
                    <option key={p} value={p}>
                      {PERSONA_LABELS[p]}
                    </option>
                  ))}
                </select>
                <svg
                  className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden
                >
                  <path
                    fillRule="evenodd"
                    d="M5.23 7.21a.75.75 0 011.06.02L10 11.06l3.71-3.83a.75.75 0 111.08 1.04l-4.25 4.39a.75.75 0 01-1.08 0L5.21 8.27a.75.75 0 01.02-1.06z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <span className="mt-1.5 block text-[12px] text-muted">
                {PERSONA_TAGLINES[persona]}
              </span>
            </label>

            <button
              type="submit"
              disabled={submitting}
              className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-[#6d70ff] py-3 text-[14px] font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:brightness-[1.05] disabled:opacity-70"
            >
              Enter workspace
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </button>
          </form>

          <p className="mt-6 text-center text-[12px] text-muted">
            Demo access — no real password or account required.
          </p>
        </div>
      </main>
    </div>
  );
}
