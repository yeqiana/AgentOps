import { createBrowserRouter, Navigate } from "react-router-dom";
import { App } from "./App";
import { TraceListPage } from "../pages/traces/TraceListPage";
import { TraceDetailEntryPage } from "../pages/traces/TraceDetailEntryPage";
import { TaskDetailPage } from "../pages/tasks/TaskDetailPage";
import { ObservabilityDashboardPage } from "../pages/observability/ObservabilityDashboardPage";
import { AlertCenterPage } from "../pages/alerts/AlertCenterPage";
import { LoginPage } from "../pages/auth/LoginPage";
import { RequireAuth } from "../features/auth/RequireAuth";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />
  },
  {
    path: "/",
    element: (
      <RequireAuth>
        <App />
      </RequireAuth>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/console/observability" replace />
      },
      {
        path: "/console",
        element: <Navigate to="/console/observability" replace />
      },
      {
        path: "/console/traces",
        element: <TraceListPage />
      },
      {
        path: "/console/observability",
        element: <ObservabilityDashboardPage />
      },
      {
        path: "/console/alerts",
        element: <AlertCenterPage />
      },
      {
        path: "/console/traces/:traceId",
        element: <TraceDetailEntryPage />
      },
      {
        path: "/console/tasks/:taskId",
        element: <TaskDetailPage />
      }
    ]
  }
]);
