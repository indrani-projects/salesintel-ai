import type { BriefStatus, Confidence } from "../api/types";

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

// Status colours use the Direction C semantic tokens:
//   ready = good · generating = warn · error = bad · pending = faint
export const STATUS_META: Record<
  BriefStatus,
  { label: string; dot: string; badge: string; event: string }
> = {
  pending: {
    label: "Pending",
    dot: "bg-faint",
    badge: "bg-ink-100 text-ink-600 border-line",
    event: "#8a93a6",
  },
  generating: {
    label: "Generating",
    dot: "bg-warn",
    badge: "border-transparent bg-[#fbf1de] text-warn",
    event: "#c07d12",
  },
  ready: {
    label: "Ready",
    dot: "bg-good",
    badge: "border-transparent bg-[#e7f6ee] text-good",
    event: "#0f9d58",
  },
  error: {
    label: "Error",
    dot: "bg-bad",
    badge: "border-transparent bg-[#fdeaec] text-bad",
    event: "#d33a4b",
  },
};

// Confidence chips: High = good · Medium = warn · Low = bad tint.
export const CONFIDENCE_META: Record<
  Confidence,
  { label: string; chip: string }
> = {
  high: { label: "High", chip: "bg-[#e7f6ee] text-good" },
  medium: { label: "Medium", chip: "bg-[#fbf1de] text-warn" },
  low: { label: "Low", chip: "bg-[#fdeaec] text-bad" },
};

export function isActiveStatus(status: BriefStatus): boolean {
  return status === "pending" || status === "generating";
}
