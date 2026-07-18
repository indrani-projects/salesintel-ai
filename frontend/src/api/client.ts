import axios from "axios";
import type {
  BriefRead,
  ChatMessageRead,
  ChatResponse,
  CalendarSyncResult,
  CompanyRead,
  EmailPreview,
  EmailSendResult,
  GoogleStatus,
  HealthResponse,
  MeetingCreate,
  MeetingRead,
  Persona,
} from "./types";

// Default targets the local backend directly. For a shared/tunnelled demo, set
// VITE_API_URL=/api so requests go same-origin through the Vite dev proxy
// (see vite.config.ts) — that lets one tunnel URL serve both frontend + API.
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export async function listCompanies(): Promise<CompanyRead[]> {
  const { data } = await api.get<CompanyRead[]>("/companies");
  return data;
}

export async function listMeetings(): Promise<MeetingRead[]> {
  const { data } = await api.get<MeetingRead[]>("/meetings");
  return data;
}

export async function createMeeting(payload: MeetingCreate): Promise<MeetingRead> {
  const { data } = await api.post<MeetingRead>("/meetings", payload);
  return data;
}

export async function getMeeting(id: number): Promise<MeetingRead> {
  const { data } = await api.get<MeetingRead>(`/meetings/${id}`);
  return data;
}

export async function deleteMeeting(id: number): Promise<void> {
  await api.delete(`/meetings/${id}`);
}

export async function getBrief(id: number, persona?: Persona): Promise<BriefRead> {
  const qs = persona ? `?persona=${persona}` : "";
  const { data } = await api.get<BriefRead>(`/meetings/${id}/brief${qs}`);
  return data;
}

export async function regenerateBrief(id: number, persona?: Persona): Promise<BriefRead> {
  const qs = persona ? `?persona=${persona}` : "";
  const { data } = await api.post<BriefRead>(`/meetings/${id}/brief/regenerate${qs}`);
  return data;
}

export async function getChat(id: number): Promise<ChatMessageRead[]> {
  const { data } = await api.get<ChatMessageRead[]>(`/meetings/${id}/chat`);
  return data;
}

export async function postChat(id: number, question: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>(`/meetings/${id}/chat`, { question });
  return data;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

// ---- Google integration ----
/** Full URL to start the OAuth connect flow (navigate the browser here). */
export const googleLoginUrl = () => `${API_BASE_URL}/auth/google/login`;

export async function getGoogleStatus(): Promise<GoogleStatus> {
  const { data } = await api.get<GoogleStatus>("/integrations/google/status");
  return data;
}

export async function syncGoogleCalendar(): Promise<CalendarSyncResult> {
  const { data } = await api.post<CalendarSyncResult>("/integrations/google/calendar/sync");
  return data;
}

export async function disconnectGoogle(): Promise<void> {
  await api.delete("/integrations/google/disconnect");
}

export async function getBriefEmailPreview(
  id: number,
  persona?: Persona,
): Promise<EmailPreview> {
  const qs = persona ? `?persona=${persona}` : "";
  const { data } = await api.get<EmailPreview>(
    `/meetings/${id}/brief/email/preview${qs}`,
  );
  return data;
}

export async function sendBriefEmail(
  id: number,
  recipient: string,
  persona?: Persona,
): Promise<EmailSendResult> {
  const qs = persona ? `?persona=${persona}` : "";
  const { data } = await api.post<EmailSendResult>(
    `/meetings/${id}/brief/email/send${qs}`,
    { recipient },
  );
  return data;
}
