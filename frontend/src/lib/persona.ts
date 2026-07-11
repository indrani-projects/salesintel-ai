import type { Persona } from "../api/types";
import { PERSONA_LABELS, PERSONA_TAGLINES } from "../api/types";

export { PERSONA_LABELS, PERSONA_TAGLINES };
export const PERSONAS: Persona[] = ["ae", "sdr", "se"];

/**
 * Subtle per-persona tint for at-a-glance differentiation. The app's primary
 * accent stays indigo (Account Executive); Sales Development Rep = emerald,
 * Solutions Engineer = amber. Full literal Tailwind class strings so the JIT
 * scanner keeps them (do NOT build these via string concatenation).
 */
export interface PersonaAccent {
  /** Small pill badge (dashboard card, brief header chip). */
  badge: string;
  /** Left border accent for banners. */
  border: string;
  /** Soft banner background gradient. */
  banner: string;
  /** Icon / eyebrow text colour. */
  text: string;
  /** Solid dot colour. */
  dot: string;
}

export const PERSONA_ACCENTS: Record<Persona, PersonaAccent> = {
  ae: {
    badge: "border-brand-200 bg-brand-50 text-brand-700",
    border: "border-brand-600",
    banner: "from-brand-50 to-transparent",
    text: "text-brand-700",
    dot: "bg-brand-600",
  },
  sdr: {
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
    border: "border-emerald-600",
    banner: "from-emerald-50/70 to-transparent",
    text: "text-emerald-700",
    dot: "bg-emerald-600",
  },
  se: {
    badge: "border-amber-200 bg-amber-50 text-amber-700",
    border: "border-amber-600",
    banner: "from-amber-50/70 to-transparent",
    text: "text-amber-700",
    dot: "bg-amber-600",
  },
};
