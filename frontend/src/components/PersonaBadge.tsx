import { UserRound } from "lucide-react";
import type { Persona } from "../api/types";
import { PERSONA_ACCENTS, PERSONA_LABELS } from "../lib/persona";

interface Props {
  persona: Persona;
  className?: string;
}

/** Full-form persona badge with a subtle per-persona tint. */
export function PersonaBadge({ persona, className = "" }: Props) {
  const accent = PERSONA_ACCENTS[persona];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${accent.badge} ${className}`}
      title={PERSONA_LABELS[persona]}
    >
      <UserRound className="h-3 w-3" />
      {PERSONA_LABELS[persona]}
    </span>
  );
}
