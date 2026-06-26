import { Navigate, Route, Routes } from "react-router-dom";

import { AdminLayout } from "@/components/AdminLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { CorpusPage } from "@/pages/CorpusPage";
import { JobsPage } from "@/pages/JobsPage";
import { HealthPage } from "@/pages/HealthPage";
import { AuditPage } from "@/pages/AuditPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/corpus" element={<CorpusPage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/health" element={<HealthPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
