import type { ChatSession } from "@/lib/answer-types";

const STORAGE_KEY = "phap-dien-next-sessions-v1";
const MAX_SESSIONS = 12;

export function loadSessions(): ChatSession[] {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(value) ? value.slice(0, MAX_SESSIONS) : [];
  } catch {
    return [];
  }
}

export function saveSessions(sessions: ChatSession[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)));
}
