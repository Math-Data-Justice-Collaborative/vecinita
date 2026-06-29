import type { ReactNode } from "react";

import { useIsAdmin } from "@/auth/authContext";

/** Renders children only for operators with the `admin` role (UJ-029). */
export function AdminWriteGate({ children }: { children: ReactNode }) {
  const isAdmin = useIsAdmin();
  if (!isAdmin) {
    return null;
  }
  return children;
}
