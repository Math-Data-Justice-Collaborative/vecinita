import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/auth/auth-context";
import { PageLoadingState } from "@/components/PageLoadingState";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <PageLoadingState />
      </div>
    );
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}
