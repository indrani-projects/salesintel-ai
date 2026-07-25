import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Download,
  Loader2,
  Mail,
  ShieldAlert,
} from "lucide-react";
import { getBrief, getMeeting } from "../api/client";
import type { BriefSection, KeyFact, Persona } from "../api/types";
import { downloadElementAsPdf, safeFilename } from "../lib/pdf";
import { MarkdownView } from "../components/MarkdownView";
import { ChatPanel } from "../components/ChatPanel";
import { EmailDialog } from "../components/EmailDialog";
import { CONFIDENCE_META, formatDateTime } from "../lib/format";
import { PERSONAS, PERSONA_LABELS } from "../lib/persona";

function KpiStrip({ facts }: { facts: KeyFact[] }) {
  const items = facts.slice(0, 4);
  if (items.length === 0) return null;
  return (
    <div className="grid grid-cols-2 gap-3.5 lg:grid-cols-4">
      {items.map((f, i) => (
        <div key={`${f.label}-${i}`} className="card p-4">
          <div className="text-xs text-muted">{f.label}</div>
          <div className="tnum mt-1 text-[22px] font-bold leading-tight tracking-tight text-ink-900">
            {f.value}
          </div>
          {f.note && <div className="mt-0.5 text-[11.5px] text-muted">{f.note}</div>}
        </div>
      ))}
    </div>
  );
}

function ConfidenceChip({ level }: { level: BriefSection["confidence"] }) {
  const meta = CONFIDENCE_META[level];
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10.5px] font-bold uppercase tracking-wide ${meta.chip}`}
    >
      {meta.label}
    </span>
  );
}

function VerifyFlag() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-[#f4c9cf] bg-[#fdeaec] px-2 py-0.5 text-[11px] font-semibold text-bad">
      <ShieldAlert className="h-3 w-3" />
      verify before use
    </span>
  );
}

function SectionCard({ section, index }: { section: BriefSection; index: number }) {
  const low = section.confidence === "low";
  return (
    <section className="card p-5 sm:p-6" id={`section-${section.id}`}>
      <div className="mb-3 flex items-center gap-2.5">
        <span className="grid h-6 w-6 place-items-center rounded-[7px] bg-brand-50 text-xs font-bold text-brand-700">
          {index + 1}
        </span>
        <h2 className="text-[15px] font-bold text-ink-900">{section.title}</h2>
        <span className="ml-auto flex items-center gap-2">
          {low && <VerifyFlag />}
          <ConfidenceChip level={section.confidence} />
        </span>
      </div>
      <MarkdownView>{section.content_md}</MarkdownView>
    </section>
  );
}

export function BriefView() {
  const { id } = useParams<{ id: string }>();
  const meetingId = Number(id);
  const briefRef = useRef<HTMLDivElement>(null);
  const [downloading, setDownloading] = useState(false);
  const [activePersona, setActivePersona] = useState<Persona | null>(null);
  const [emailOpen, setEmailOpen] = useState(false);

  const { data: meeting } = useQuery({
    queryKey: ["meeting", meetingId],
    queryFn: () => getMeeting(meetingId),
    enabled: Number.isFinite(meetingId),
  });

  // Initialize the viewed persona to the meeting's primary persona once loaded.
  useEffect(() => {
    if (meeting && activePersona === null) {
      setActivePersona(meeting.persona);
    }
  }, [meeting, activePersona]);

  const viewPersona: Persona = activePersona ?? meeting?.persona ?? "sales_rep";

  const { data: brief, isLoading } = useQuery({
    queryKey: ["brief", meetingId, viewPersona],
    queryFn: () => getBrief(meetingId, viewPersona),
    enabled: Number.isFinite(meetingId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "generating" ? 4000 : false;
    },
  });

  const status = brief?.status ?? meeting?.brief_status;
  const ready = status === "ready" && brief?.content;
  const company = brief?.content?.company ?? meeting?.prospect_company ?? "Brief";

  const handleDownload = async () => {
    if (!briefRef.current) return;
    setDownloading(true);
    try {
      const base = safeFilename(meeting?.subject ?? brief?.content?.company ?? "brief");
      await downloadElementAsPdf(briefRef.current, `${base}-${viewPersona}.pdf`);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div>
      {/* Top bar: breadcrumb + "View as" segmented control */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-[13px] text-muted">
            <Link to="/dashboard" className="hover:text-brand-700">
              Briefs
            </Link>{" "}
            / <b className="font-semibold text-ink-900">{company}</b>
          </div>
          {meeting && (
            <div className="mt-0.5 text-xs text-faint">
              {meeting.subject} · {formatDateTime(meeting.start_time)}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className="seg" role="tablist" aria-label="View as persona">
            {PERSONAS.map((p) => {
              const active = viewPersona === p;
              return (
                <button
                  key={p}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setActivePersona(p)}
                  className={`seg-btn ${active ? "on" : ""}`}
                >
                  {PERSONA_LABELS[p]}
                </button>
              );
            })}
          </div>
          {ready && (
            <>
              <button
                className="btn-secondary"
                onClick={() => setEmailOpen(true)}
              >
                <Mail className="h-4 w-4" />
                Send as email
              </button>
              <button className="btn-primary" onClick={handleDownload} disabled={downloading}>
                {downloading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Download PDF
              </button>
            </>
          )}
        </div>
      </div>

      {ready && (
        <EmailDialog
          open={emailOpen}
          onClose={() => setEmailOpen(false)}
          meetingId={meetingId}
          persona={viewPersona}
        />
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
        {/* Brief column */}
        <div className="min-w-0">
          {isLoading && (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="card h-32 animate-pulse bg-ink-100/60" />
              ))}
            </div>
          )}

          {!isLoading && (status === "pending" || status === "generating") && (
            <div className="card flex flex-col items-center justify-center gap-3 p-16 text-center">
              <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
              <div>
                <h3 className="text-base font-semibold text-ink-900">
                  Preparing this brief…
                </h3>
                <p className="mt-1 max-w-sm text-sm text-muted">
                  SalesIntel AI is researching {meeting?.prospect_company ?? "the prospect"} and
                  synthesizing the {PERSONA_LABELS[viewPersona]} brief. This updates
                  automatically.
                </p>
              </div>
            </div>
          )}

          {!isLoading && status === "error" && (
            <div className="card flex flex-col items-center justify-center gap-3 p-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#fdeaec] text-bad">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-ink-900">
                  Brief generation failed
                </h3>
                <p className="mt-1 max-w-sm text-sm text-muted">
                  {brief?.error ?? "An unexpected error occurred."} Try regenerating from the
                  briefs dashboard.
                </p>
              </div>
            </div>
          )}

          {ready && brief?.content && (
            <div ref={briefRef} className="space-y-4">
              {/* KPI strip (older briefs may not carry key_facts) */}
              <KpiStrip facts={brief.content.key_facts ?? []} />

              {/* Hero card */}
              <section className="card p-6 sm:p-7">
                <span className="inline-block rounded-full bg-brand-50 px-3 py-1 text-[11.5px] font-bold text-brand-700">
                  {PERSONA_LABELS[viewPersona]} · Brief
                </span>
                <h1 className="mt-3 text-[26px] font-bold leading-tight tracking-tight text-ink-900 text-balance">
                  {brief.content.company}
                </h1>
                {brief.content.headline && (
                  <p className="mt-1.5 max-w-[62ch] text-[15px] text-ink-700">
                    {brief.content.headline}
                  </p>
                )}
                <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-[#e7f6ee] px-2.5 py-1 text-xs font-semibold text-good">
                  <span className="h-1.5 w-1.5 rounded-full bg-good" />
                  Ready · {brief.content.sources.length} source
                  {brief.content.sources.length === 1 ? "" : "s"}
                </span>
              </section>

              {brief.content.sections.map((s, i) => (
                <SectionCard key={s.id} section={s} index={i} />
              ))}

              {/* Sources */}
              {brief.content.sources.length > 0 && (
                <section className="card p-5 sm:p-6">
                  <h2 className="mb-3 text-[15px] font-bold text-ink-900">Sources</h2>
                  <ul className="space-y-2">
                    {brief.content.sources.map((src) => (
                      <li key={src.marker} className="flex gap-2 text-sm text-ink-600">
                        <span className="mt-0.5 shrink-0 rounded bg-brand-50 px-1.5 py-0.5 text-xs font-semibold text-brand-700">
                          {src.marker}
                        </span>
                        <span className="min-w-0">
                          <span className="font-medium text-ink-800">{src.title}</span>
                          {src.filename && (
                            <span className="text-faint"> — {src.filename}</span>
                          )}
                          {src.url && (
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noreferrer"
                              className="ml-1 text-brand-600 underline underline-offset-2"
                            >
                              link
                            </a>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
          )}
        </div>

        {/* Scout column */}
        <div className="lg:sticky lg:top-6 lg:h-[calc(100vh-6rem)]">
          <ChatPanel meetingId={meetingId} disabled={!ready} />
        </div>
      </div>
    </div>
  );
}
