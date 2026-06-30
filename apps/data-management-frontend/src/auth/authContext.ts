import { createContext, useContext } from "react";
import type { Session, User } from "@supabase/supabase-js";

import type { OperatorRole } from "@/auth/supabaseClient";

export interface AuthState {
  session: Session | null;
  user: User | null;
  role: OperatorRole | null;
  loading: boolean;
  accessToken: string | null;
  signIn: (email: string, password: string, remember?: boolean) => Promise<void>;
  signOut: () => Promise<void>;
  signOutAllDevices: () => Promise<void>;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

export function useIsAdmin(): boolean {
  const { role } = useAuth();
  return role === "admin";
}
