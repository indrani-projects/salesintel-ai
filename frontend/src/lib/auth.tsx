// Lightweight client-side "auth" for the demo — NOT real authentication. It just
// remembers the signed-in user's name and their selected persona in localStorage so
// the app can personalize the workspace and default new briefs to that persona.
import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { Persona } from "../api/types";

export interface AuthUser {
  name: string;
  persona: Persona;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (user: AuthUser) => void;
  logout: () => void;
}

const STORAGE_KEY = "salesintel.auth";
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStored(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.name === "string" && typeof parsed.persona === "string") {
      return { name: parsed.name, persona: parsed.persona as Persona };
    }
  } catch {
    /* ignore malformed storage */
  }
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => readStored());

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      login: (u) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
        setUser(u);
      },
      logout: () => {
        localStorage.removeItem(STORAGE_KEY);
        setUser(null);
      },
    }),
    [user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

/** Initials for the avatar chip, e.g. "Rohan M." → "RM". */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "U";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
