import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  CalendarClock,
  Download,
  FileText,
  Loader2,
  RefreshCw,
  Trash2,
} from "lucide-react";
import type { MeetingRead } from "../api/types";
import { deleteMeeting, getBrief, regenerateBrief } from "../api/client";
import { formatDateTime } from "../lib/format";
import { downloadElementAsPdf, safeFilename } from "../lib/pdf";
import { StatusBadge } from "./StatusBadge";
import { PersonaBadge } from "./PersonaBadge";
import { renderBriefToHtml } from "../lib/briefHtml";

export function BriefCard({ meeting }: { meeting: MeetingRead }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [downloading, setDownloading] = useState(false);

  const regen = useMutation({
    mutationFn: () => regenerateBrief(meeting.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });

  const del = useMutation({
    mutationFn: () => deleteMeeting(meeting.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });

  const isReady = meeting.brief_status === "ready";
  const isError = meeting.brief_status === "error";

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const brief = await getBrief(meeting.id);
      if (!brief.content) return;
      const holder = document.createElement("div");
      holder.style.width = "780px";
      holder.style.padding = "8px";
      holder.innerHTML = renderBriefToHtml(brief.content);
      document.body.appendChild(holder);
      await downloadElementAsPdf(
        holder,
        `${safeFilename(meeting.subject || "brief")}.pdf`,
      );
      document.body.removeChild(holder);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="card group flex flex-col p-5 transition-shadow hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-semibold leading-snug text-ink-900 line-clamp-2">
          {meeting.subject}
        </h3>
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <StatusBadge status={meeting.brief_status} />
          <PersonaBadge persona={meeting.persona} />
        </div>
      </div>

      <div className="mt-3 space-y-1.5 text-sm text-ink-500">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 shrink-0 text-ink-400" />
          <span className="truncate">{meeting.prospect_company}</span>
        </div>
        <div className="flex items-center gap-2">
          <CalendarClock className="h-4 w-4 shrink-0 text-ink-400" />
          <span>{formatDateTime(meeting.start_time)}</span>
        </div>
      </div>

      {isError && (
        <p className="mt-3 rounded-lg bg-[#fdeaec] px-3 py-2 text-xs font-medium text-bad">
          Brief generation failed. Try regenerating.
        </p>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-line2 pt-4">
        <button
          className="btn-primary flex-1"
          disabled={!isReady}
          onClick={() => navigate(`/meeting/${meeting.id}`)}
        >
          <FileText className="h-4 w-4" />
          View brief
        </button>
        <button
          className="btn-secondary"
          disabled={!isReady || downloading}
          onClick={handleDownload}
          title="Download PDF"
        >
          {downloading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
        </button>
        <button
          className="btn-ghost"
          disabled={regen.isPending}
          onClick={() => regen.mutate()}
          title="Regenerate brief"
        >
          <RefreshCw className={`h-4 w-4 ${regen.isPending ? "animate-spin" : ""}`} />
        </button>
        <button
          className="btn-ghost text-bad hover:bg-[#fdeaec] hover:text-bad"
          disabled={del.isPending}
          onClick={() => del.mutate()}
          title="Delete meeting"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
