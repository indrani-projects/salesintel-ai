import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CalendarPlus, Inbox, Loader2, RefreshCw } from "lucide-react";
import { listMeetings } from "../api/client";
import type { MeetingRead } from "../api/types";
import { isActiveStatus } from "../lib/format";
import { BriefCard } from "../components/BriefCard";
import { MeetingDialog } from "../components/MeetingDialog";

export function DashboardPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: meetings = [], isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["meetings"],
    queryFn: listMeetings,
    // Poll fast (4s) while a brief is generating; otherwise keep a slower idle poll
    // (15s) so meetings the background Google-sync imports appear without a manual
    // refresh. (Never stops — matches the recurring backend calendar sync.)
    refetchInterval: (query) => {
      const list = (query.state.data as MeetingRead[] | undefined) ?? [];
      return list.some((m) => isActiveStatus(m.brief_status)) ? 4000 : 15000;
    },
  });

  const activeCount = meetings.filter((m) => isActiveStatus(m.brief_status)).length;
  const sorted = [...meetings].sort(
    (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime(),
  );

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[13px] text-muted">
            <b className="font-semibold text-ink-900">Briefs</b>
          </div>
          <p className="mt-0.5 text-sm text-muted">
            {meetings.length > 0
              ? `${meetings.length} meeting${meetings.length === 1 ? "" : "s"}`
              : "Your generated pre-call briefs live here."}
            {activeCount > 0 && (
              <span className="ml-2 inline-flex items-center gap-1 text-warn">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                {activeCount} generating…
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button className="btn-primary" onClick={() => setDialogOpen(true)}>
            <CalendarPlus className="h-4 w-4" />
            New meeting
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card h-44 animate-pulse bg-ink-100/50" />
          ))}
        </div>
      )}

      {isError && (
        <div className="card flex flex-col items-center justify-center gap-3 p-12 text-center">
          <p className="text-sm text-ink-600">
            Couldn't reach the backend at <code>localhost:8000</code>.
          </p>
          <button className="btn-secondary" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
        </div>
      )}

      {!isLoading && !isError && sorted.length === 0 && (
        <div className="card flex flex-col items-center justify-center gap-4 p-16 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-500">
            <Inbox className="h-7 w-7" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-ink-900">No briefs yet</h3>
            <p className="mt-1 max-w-sm text-sm text-ink-500">
              Schedule a meeting from the calendar and SalesIntel AI will research the
              prospect and prepare a brief automatically.
            </p>
          </div>
          <button className="btn-primary" onClick={() => setDialogOpen(true)}>
            <CalendarPlus className="h-4 w-4" />
            Create your first meeting
          </button>
        </div>
      )}

      {!isLoading && !isError && sorted.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sorted.map((m) => (
            <BriefCard key={m.id} meeting={m} />
          ))}
        </div>
      )}

      <MeetingDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </div>
  );
}
