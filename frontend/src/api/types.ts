// Mirrors backend/app/schemas.py — keep in sync with the shared contract.

export type BriefStatus = "pending" | "generating" | "ready" | "error";

export type Confidence = "high" | "medium" | "low";

export type Persona = "ae" | "sdr" | "se";

export const PERSONA_ORDER: Persona[] = ["ae", "sdr", "se"];

export const PERSONA_LABELS: Record<Persona, string> = {
  ae: "Account Executive",
  sdr: "Sales Development Rep",
  se: "Solutions Engineer",
};

export const PERSONA_TAGLINES: Record<Persona, string> = {
  ae: "Full pre-call brief — discovery to close",
  sdr: "Prospecting brief — earn the meeting",
  se: "Technical fit brief — prep the deep-dive",
};

// The nine fixed sections of every brief, in display order.
export const SECTION_ORDER = [
  "company_snapshot",
  "financials",
  "trigger_events",
  "gtm_model",
  "pain_hypotheses",
  "tech_stack",
  "stakeholders",
  "risks",
  "recommended_angle",
] as const;

export const SECTION_TITLES: Record<string, string> = {
  company_snapshot: "Company Snapshot",
  financials: "Financial & Funding Health",
  trigger_events: "Trigger Events / Recent News",
  gtm_model: "GTM & Operating Model",
  pain_hypotheses: "Pain Hypotheses → Mapped to Zoho",
  tech_stack: "Tech Stack Signals",
  stakeholders: "Key Stakeholders",
  risks: "Risks & Watch-outs",
  recommended_angle: "Analyst's Recommended Angle",
};

export interface CompanyRead {
  slug: string;
  name: string;
  doc_count: number;
}

export interface MeetingCreate {
  subject: string;
  prospect_company: string;
  why?: string;
  agenda?: string;
  start_time: string; // ISO datetime
  persona?: Persona;
}

export interface MeetingRead {
  id: number;
  subject: string;
  prospect_company: string;
  company_slug?: string | null;
  why: string;
  agenda: string;
  start_time: string;
  created_at: string;
  brief_status: BriefStatus;
  persona: Persona;
  google_event_id?: string | null;
  google_html_link?: string | null;
}

export interface BriefSource {
  marker: string;
  title: string;
  filename?: string | null;
  url?: string | null;
}

export interface BriefSection {
  id: string;
  title: string;
  content_md: string;
  confidence: Confidence;
  flags: string[];
}

export interface KeyFact {
  label: string;
  value: string;
  note?: string | null;
}

export interface BriefContent {
  company: string;
  company_slug: string;
  persona: Persona;
  headline: string;
  key_facts?: KeyFact[];
  sections: BriefSection[];
  sources: BriefSource[];
  generated_at?: string | null;
}

export interface BriefRead {
  meeting_id: number;
  persona?: Persona;
  status: BriefStatus;
  content?: BriefContent | null;
  html?: string | null;
  error?: string | null;
}

export interface ChatRequest {
  question: string;
}

export interface ChatResponse {
  answer_md: string;
  citations: BriefSource[];
  grounded: boolean;
}

export interface ChatMessageRead {
  id: number;
  meeting_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  llm_configured: boolean;
}

export interface EmailPreview {
  subject: string;
  body_html: string;
  attachment_filename: string;
  recipient_default: string;
  email_configured: boolean;
}

export interface EmailSendResult {
  delivered: boolean;
  mode: "sent" | "demo" | "error" | "gmail";
  recipient: string;
  subject: string;
  message: string;
}

export interface GoogleStatus {
  configured: boolean;
  connected: boolean;
  email?: string | null;
  scopes: string[];
}

export interface CalendarSyncResult {
  imported: number;
  briefed: number;
  skipped_existing: number;
  scanned: number;
  message: string;
}

export interface EmailAutomationStatus {
  enabled: boolean;
  lead_minutes: number;
  recipient: string;
  transport: "gmail" | "smtp" | "demo";
}
