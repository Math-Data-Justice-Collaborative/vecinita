import { createBrowserRouter } from "react-router";
import { createElement } from "react";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { CorpusView } from "./pages/CorpusView";
import { AddDocument } from "./pages/AddDocument";
import { DocumentDetail } from "./pages/DocumentDetail";
import { ScrapeJobs } from "./pages/ScrapeJobs";
import { TagsView } from "./pages/TagsView";
import { Settings } from "./pages/Settings";
import { AdminAccess } from "./pages/AdminAccess";
import { Login } from "./pages/Login";
import { RequireAuth } from "./auth/RequireAuth";

function ProtectedLayout() {
  return createElement(
    RequireAuth,
    null,
    createElement(Layout),
  );
}

export const router = createBrowserRouter([
  { path: "/login", Component: Login },
  {
    path: "/",
    Component: ProtectedLayout,
    children: [
      { index: true, Component: Dashboard },
      { path: "corpus", Component: CorpusView },
      { path: "add", Component: AddDocument },
      { path: "document/:id", Component: DocumentDetail },
      { path: "scrape-jobs", Component: ScrapeJobs },
      { path: "tags", Component: TagsView },
      { path: "settings", Component: Settings },
      { path: "admin-access", Component: AdminAccess },
    ],
  },
]);