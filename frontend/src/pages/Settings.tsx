import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowUpRight,
  BookOpen,
  CalendarCheck,
  CheckCircle2,
  Clock,
  FileText,
  Library,
  ListChecks,
  Loader2,
  Mail,
  RefreshCw,
  Send,
  Unplug,
  Wrench,
} from "lucide-react";
import {
  disconnectGoogle,
  getEmailAutomation,
  getGoogleStatus,
  googleLoginUrl,
  syncGoogleCalendar,
} from "../api/client";
import type { CalendarSyncResult } from "../api/types";

// Developer Library — help/reference docs served as static pages at /library/*
// (generated at build time by frontend/scripts/build-library.mjs). Open in a new tab.
const LIBRARY = [
  {
    href: "/library/how-it-works.html",
    title: "How It Works",
    blurb: "A plain-English tour of the tech and how a briefing is built.",
    Icon: BookOpen,
  },
  {
    href: "/library/project-tracker.html",
    title: "Build Tracker",
    blurb: "Every feature we've shipped, grouped by phase.",
    Icon: ListChecks,
  },
  {
    href: "/library/runbook.html",
    title: "Operations Runbook",
    blurb: "Setup, running, deployment, and troubleshooting.",
    Icon: Wrench,
  },
  {
    href: "/library/build-plan.html",
    title: "Architecture & Build Plan",
    blurb: "The design, tech stack, and product roadmap.",
    Icon: FileText,
  },
];

export function SettingsPage() {
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [banner, setBanner] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [sync, setSync] = useState<CalendarSyncResult | null>(null);

  const { data: status, isLoading } = useQuery({
    queryKey: ["google-status"],
    queryFn: getGoogleStatus,
    refetchOnWindowFocus: true,
  });

  const { data: automation } = useQuery({
    queryKey: ["email-automation"],
    queryFn: getEmailAutomation,
  });

  // React to the OAuth callback redirect (?google=connected|error).
  useEffect(() => {
    const g = params.get("google");
    if (!g) return;
    if (g === "connected") setBanner({ kind: "ok", text: "Google account connected." });
    if (g === "error") setBanner({ kind: "err", text: "Could not connect Google — please try again." });
    qc.invalidateQueries({ queryKey: ["google-status"] });
    params.delete("google");
    setParams(params, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const syncMutation = useMutation({
    mutationFn: syncGoogleCalendar,
    onSuccess: (res) => {
      setSync(res);
      qc.invalidateQueries({ queryKey: ["meetings"] });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: disconnectGoogle,
    onSuccess: () => {
      setSync(null);
      setBanner(null);
      qc.invalidateQueries({ queryKey: ["google-status"] });
    },
  });

  const connected = !!status?.connected;
  const configured = !!status?.configured;

  return (
    <div className="max-w-3xl">
      <h1 className="text-[22px] font-bold tracking-tight text-ink-900">Settings</h1>
      <p className="mt-1 text-sm text-muted">Connect the tools SalesIntel works with.</p>

      {banner && (
        <div
          className={`mt-4 flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${
            banner.kind === "ok" ? "bg-[#e7f6ee] text-good" : "bg-[#fdeaec] text-bad"
          }`}
        >
          {banner.kind === "ok" ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          {banner.text}
        </div>
      )}

      {/* Google card */}
      <section className="card mt-5 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
              <CalendarCheck className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-ink-900">Google (Gmail + Calendar)</h2>
              <p className="mt-0.5 max-w-md text-[13px] text-muted">
                One connection: send brief emails from your Gmail, and sync your Google
                Calendar so prospect meetings auto-generate briefs.
              </p>
            </div>
          </div>
          {isLoading ? (
            <Loader2 className="mt-1 h-5 w-5 animate-spin text-muted" />
          ) : connected ? (
            <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-[#e7f6ee] px-2.5 py-1 text-xs font-semibold text-good">
              <span className="h-1.5 w-1.5 rounded-full bg-good" />
              Connected
            </span>
          ) : (
            <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 text-xs font-semibold text-muted">
              Not connected
            </span>
          )}
        </div>

        <div className="mt-5 border-t border-line pt-4">
          {!configured && !connected && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-[13px] text-amber-700">
              Google isn't set up on the server yet. Add <code>GOOGLE_CLIENT_ID</code> /
              <code> GOOGLE_CLIENT_SECRET</code> to <code>backend/.env</code> and restart —
              see <b>docs/RUNBOOK.md</b> for the ~15-min Google Cloud setup.
            </p>
          )}

          {configured && !connected && (
            <a href={googleLoginUrl()} className="btn-primary inline-flex w-fit">
              <Mail className="h-4 w-4" />
              Connect Google
            </a>
          )}

          {connected && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-ink-700">
                <CheckCircle2 className="h-4 w-4 text-good" />
                Connected as <b className="font-semibold">{status?.email ?? "your Google account"}</b>
              </div>

              <div className="flex flex-wrap items-center gap-2.5">
                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                >
                  {syncMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  Sync calendar now
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => disconnectMutation.mutate()}
                  disabled={disconnectMutation.isPending}
                >
                  <Unplug className="h-4 w-4" />
                  Disconnect
                </button>
              </div>

              {sync && (
                <p className="rounded-lg bg-ink-50 px-3 py-2 text-[13px] text-ink-700">
                  {sync.message}
                </p>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Automated emails card (read-only) */}
      <section className="card mt-5 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
              <Send className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-ink-900">Automated emails</h2>
              <p className="mt-0.5 max-w-md text-[13px] text-muted">
                Each brief is emailed automatically when it's ready, and again about an
                hour before the meeting.
              </p>
            </div>
          </div>
          {automation ? (
            automation.enabled ? (
              <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-[#e7f6ee] px-2.5 py-1 text-xs font-semibold text-good">
                <span className="h-1.5 w-1.5 rounded-full bg-good" />
                On
              </span>
            ) : (
              <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-ink-100 px-2.5 py-1 text-xs font-semibold text-muted">
                Off
              </span>
            )
          ) : (
            <Loader2 className="mt-1 h-5 w-5 animate-spin text-muted" />
          )}
        </div>

        {automation && (
          <div className="mt-5 space-y-2.5 border-t border-line pt-4 text-sm text-ink-700">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-good" />
              On ready: the brief is sent as soon as it's generated.
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-brand-700" />
              Before the meeting: the brief is sent when it's within{" "}
              <b className="font-semibold">{automation.lead_minutes} min</b> of the start time.
            </div>
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-muted" />
              Sent to{" "}
              <b className="font-semibold">
                {automation.personalized
                  ? "each meeting's persona address"
                  : automation.recipient || "— (set DEFAULT_RECIPIENT)"}
              </b>
              <span className="text-muted">
                ·{" "}
                {automation.transport === "gmail"
                  ? "via your Gmail"
                  : automation.transport === "smtp"
                    ? "via SMTP"
                    : "demo (not delivered)"}
              </span>
            </div>
          </div>
        )}
      </section>

      {/* Developer Library card */}
      <section className="card mt-5 p-6">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
            <Library className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-ink-900">Developer Library</h2>
            <p className="mt-0.5 max-w-md text-[13px] text-muted">
              Guides and reference for how SalesIntel works — the technology, what's
              shipped, and how it's run and deployed.
            </p>
          </div>
        </div>

        <div className="mt-5 grid gap-2.5 border-t border-line pt-4 sm:grid-cols-2">
          {LIBRARY.map(({ href, title, blurb, Icon }) => (
            <a
              key={href}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-start gap-3 rounded-xl border border-line p-3.5 transition hover:border-brand-300 hover:bg-brand-50"
            >
              <Icon className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" />
              <div className="min-w-0">
                <div className="flex items-center gap-1 text-sm font-semibold text-ink-900">
                  {title}
                  <ArrowUpRight className="h-3.5 w-3.5 text-muted transition group-hover:text-brand-700" />
                </div>
                <p className="mt-0.5 text-[12.5px] leading-snug text-muted">{blurb}</p>
              </div>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
