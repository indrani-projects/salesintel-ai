import axios from "axios";
import type {
  BriefRead,
  ChatMessageRead,
  ChatResponse,
  CompanyRead,
  HealthResponse,
  MeetingCreate,
  MeetingRead,
  Persona,
} from "./types";

export const API_BASE_URL = "http://localhost:8000";

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
