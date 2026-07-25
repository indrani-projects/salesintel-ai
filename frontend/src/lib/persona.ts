import type { Persona } from "../api/types";
import { PERSONA_LABELS, PERSONA_TAGLINES } from "../api/types";

export { PERSONA_LABELS, PERSONA_TAGLINES };
export const PERSONAS: Persona[] = [
  "sales_rep",
  "sales_manager",
  "enablement",
  "revops",
  "vp_sales",
  "admin",
];

/**
 * Subtle per-persona tint for at-a-glance differentiation. One distinct colour per
 * persona: Sales Representative = brand indigo, Sales Manager = emerald, Sales
 * Enablement = amber, Revenue Operations = sky, VP of Sales = violet, Admin = slate.
 * Full literal Tailwind class strings so the JIT scanner keeps them (do NOT build
 * these via string concatenation).
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
  sales_rep: {
    badge: "border-brand-200 bg-brand-50 text-brand-700",
    border: "border-brand-600",
    banner: "from-brand-50 to-transparent",
    text: "text-brand-700",
    dot: "bg-brand-600",
  },
  sales_manager: {
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
    border: "border-emerald-600",
    banner: "from-emerald-50/70 to-transparent",
    text: "text-emerald-700",
    dot: "bg-emerald-600",
  },
  enablement: {
    badge: "border-amber-200 bg-amber-50 text-amber-700",
    border: "border-amber-600",
    banner: "from-amber-50/70 to-transparent",
    text: "text-amber-700",
    dot: "bg-amber-600",
  },
  revops: {
    badge: "border-sky-200 bg-sky-50 text-sky-700",
    border: "border-sky-600",
    banner: "from-sky-50/70 to-transparent",
    text: "text-sky-700",
    dot: "bg-sky-600",
  },
  vp_sales: {
    badge: "border-violet-200 bg-violet-50 text-violet-700",
    border: "border-violet-600",
    banner: "from-violet-50/70 to-transparent",
    text: "text-violet-700",
    dot: "bg-violet-600",
  },
  admin: {
    badge: "border-slate-300 bg-slate-100 text-slate-700",
    border: "border-slate-600",
    banner: "from-slate-100/70 to-transparent",
    text: "text-slate-700",
    dot: "bg-slate-600",
  },
};
