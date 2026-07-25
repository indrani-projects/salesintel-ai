import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarPlus, Loader2, X } from "lucide-react";
import { createMeeting, listCompanies } from "../api/client";
import type { CompanyRead, MeetingCreate, Persona } from "../api/types";
import { PERSONA_ACCENTS, PERSONA_LABELS, PERSONA_TAGLINES } from "../lib/persona";
import { useAuth } from "../lib/auth";

// Any company works (we pull live web intel by name); these are the research
// guide's 5 targets, offered as autocomplete suggestions.
const WEB_SUGGESTIONS = ["Freshworks", "Braze", "Sprout Social", "Amplitude", "Zuora"];

interface Props {
  open: boolean;
  onClose: () => void;
  /** ISO string to prefill the start-time field (from a calendar click). */
  initialStart?: string;
}

/** Convert an ISO string to the value a <input type="datetime-local"> expects. */
function toLocalInput(iso?: string): string {
  const d = iso ? new Date(iso) : new Date();
  if (Number.isNaN(d.getTime())) return "";
  const off = d.getTimezoneOffset();
  const local = new Date(d.getTime() - off * 60_000);
  return local.toISOString().slice(0, 16);
}

export function MeetingDialog({ open, onClose, initialStart }: Props) {
  const queryClient = useQueryClient();
  const { data: companies = [] } = useQuery({
    queryKey: ["companies"],
    queryFn: listCompanies,
    enabled: open,
  });

  const [subject, setSubject] = useState("");
  const [company, setCompany] = useState("");
  const [why, setWhy] = useState("");
  const [agenda, setAgenda] = useState("");
  const [start, setStart] = useState(toLocalInput(initialStart));
  const { user } = useAuth();
  const defaultPersona: Persona = user?.persona ?? "sales_rep";
  const [persona, setPersona] = useState<Persona>(defaultPersona);

  useEffect(() => {
    if (open) {
      setSubject("");
      setCompany("");
      setWhy("");
      setAgenda("");
      setStart(toLocalInput(initialStart));
      setPersona(defaultPersona);
    }
  }, [open, initialStart, defaultPersona]);

  const mutation = useMutation({
    mutationFn: (payload: MeetingCreate) => createMeeting(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      onClose();
    },
  });

  if (!open) return null;

  const canSubmit = subject.trim() && company && start && !mutation.isPending;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    mutation.mutate({
      subject: subject.trim(),
      prospect_company: company,
      why: why.trim(),
      agenda: agenda.trim(),
      start_time: new Date(start).toISOString(),
      persona,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      <div
        className="absolute inset-0 bg-ink-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative z-10 w-full max-w-lg animate-fade-in rounded-2xl border border-ink-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
              <CalendarPlus className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-ink-900">New Meeting</h2>
              <p className="text-xs text-ink-500">
                A pre-call brief generates automatically.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-600"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 px-6 py-5">
          <div>
            <label className="label" htmlFor="m-subject">
              Subject
            </label>
            <input
              id="m-subject"
              className="input"
              placeholder="Discovery call with The Sleep Company"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              autoFocus
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="m-company">
                Prospect company
              </label>
              <input
                id="m-company"
                className="input"
                list="m-company-suggestions"
                placeholder="Type any company (e.g. Freshworks)"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                autoComplete="off"
              />
              <datalist id="m-company-suggestions">
                {companies.map((c: CompanyRead) => (
                  <option key={c.slug} value={c.name} />
                ))}
                {WEB_SUGGESTIONS.map((n) => (
                  <option key={n} value={n} />
                ))}
              </datalist>
            </div>
            <div>
              <label className="label" htmlFor="m-start">
                Start time
              </label>
              <input
                id="m-start"
                type="datetime-local"
                className="input"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="label" htmlFor="m-why">
              Why this meeting
            </label>
            <textarea
              id="m-why"
              className="input min-h-[70px] resize-y"
              placeholder="What we want to get out of this call…"
              value={why}
              onChange={(e) => setWhy(e.target.value)}
            />
          </div>

          <div>
            <label className="label" htmlFor="m-agenda">
              Agenda
            </label>
            <textarea
              id="m-agenda"
              className="input min-h-[70px] resize-y"
              placeholder="Talking points; steers which angle the brief emphasizes…"
              value={agenda}
              onChange={(e) => setAgenda(e.target.value)}
            />
          </div>

          <div>
            <label className="label">Brief persona</label>
            {/* Single-persona app: the brief is always prepared for the signed-in role. */}
            <div className="flex items-center gap-2.5 rounded-[10px] border border-line bg-ink-50 p-3">
              <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${PERSONA_ACCENTS[persona].dot}`} />
              <div className="leading-tight">
                <div className="text-[13px] font-semibold text-ink-900">
                  {PERSONA_LABELS[persona]}
                </div>
                <div className="text-[11px] text-muted">{PERSONA_TAGLINES[persona]} · your role</div>
              </div>
            </div>
          </div>

          {mutation.isError && (
            <p className="rounded-lg bg-[#fdeaec] px-3 py-2 text-sm font-medium text-bad">
              Could not create the meeting. Is the backend running?
            </p>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={!canSubmit}>
              {mutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Create meeting
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
