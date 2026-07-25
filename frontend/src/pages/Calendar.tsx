import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { DateSelectArg, EventClickArg } from "@fullcalendar/core";
import { Loader2, Plus, RefreshCw } from "lucide-react";
import { getGoogleStatus, listMeetings, syncGoogleCalendar } from "../api/client";
import type { MeetingRead } from "../api/types";
import { STATUS_META, isActiveStatus } from "../lib/format";
import { MeetingDialog } from "../components/MeetingDialog";

export function CalendarPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [initialStart, setInitialStart] = useState<string | undefined>();

  const { data: meetings = [] } = useQuery({
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

  const { data: google } = useQuery({ queryKey: ["google-status"], queryFn: getGoogleStatus });

  const syncMutation = useMutation({
    mutationFn: syncGoogleCalendar,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });

  const events = useMemo(
    () =>
      meetings.map((m) => ({
        id: String(m.id),
        title: m.subject,
        start: m.start_time,
        backgroundColor: STATUS_META[m.brief_status].event,
        borderColor: STATUS_META[m.brief_status].event,
        extendedProps: { meetingId: m.id },
      })),
    [meetings],
  );

  const openNew = (start?: string) => {
    setInitialStart(start);
    setDialogOpen(true);
  };

  const handleSelect = (sel: DateSelectArg) => openNew(sel.start.toISOString());
  const handleEventClick = (arg: EventClickArg) => {
    const id = arg.event.extendedProps.meetingId as number;
    const meeting = meetings.find((m) => m.id === id);
    if (meeting && meeting.brief_status === "ready") navigate(`/meeting/${id}`);
    else navigate(`/dashboard`);
  };

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[13px] text-muted">
            <b className="font-semibold text-ink-900">Calendar</b>
          </div>
          <p className="mt-0.5 text-sm text-muted">
            Click any day or time slot to schedule a meeting and auto-generate a brief.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {google?.connected && (
            <button
              className="btn-secondary"
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              title="Import prospect meetings from your Google Calendar"
            >
              {syncMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Sync Google
            </button>
          )}
          <button className="btn-primary" onClick={() => openNew()}>
            <Plus className="h-4 w-4" />
            New meeting
          </button>
        </div>
      </div>

      <div className="card p-4 sm:p-5">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay",
          }}
          height="auto"
          selectable
          selectMirror
          dayMaxEvents={3}
          nowIndicator
          events={events}
          select={handleSelect}
          eventClick={handleEventClick}
          eventTimeFormat={{ hour: "numeric", minute: "2-digit", meridiem: "short" }}
        />
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-muted">
        {(["pending", "generating", "ready", "error"] as const).map((s) => (
          <span key={s} className="flex items-center gap-1.5">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: STATUS_META[s].event }}
            />
            {STATUS_META[s].label}
          </span>
        ))}
      </div>

      <MeetingDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        initialStart={initialStart}
      />
    </div>
  );
}
