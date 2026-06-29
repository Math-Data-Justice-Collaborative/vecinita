import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { AdminLayout } from "@/components/AdminLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { CorpusPage } from "@/pages/CorpusPage";
import { JobsPage } from "@/pages/JobsPage";
import { HealthPage } from "@/pages/HealthPage";
import { AuditPage } from "@/pages/AuditPage";
import { LoginPage } from "@/pages/LoginPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/corpus" element={<CorpusPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/health" element={<HealthPage />} />
        <Route path="/audit" element={<AuditPage />} />
      </Route>
      {/* Top-level splat: nested `path="*"` does not match unknown absolute paths (RR6). */}
      <Route
        path="*"
        element={
          <ProtectedRoute>
            <Navigate to="/dashboard" replace />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
