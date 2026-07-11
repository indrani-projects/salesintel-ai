import { Loader2 } from "lucide-react";
import type { BriefStatus } from "../api/types";
import { STATUS_META } from "../lib/format";

export function StatusBadge({ status }: { status: BriefStatus }) {
  const meta = STATUS_META[status];
  const spinning = status === "generating";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${meta.badge}`}
    >
      {spinning ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
      )}
      {meta.label}
    </span>
  );
}
