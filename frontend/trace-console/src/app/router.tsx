import { createBrowserRouter, Navigate } from "react-router-dom";
import { App } from "./App";
import { TraceListPage } from "../pages/traces/TraceListPage";
import { TraceDetailEntryPage } from "../pages/traces/TraceDetailEntryPage";
import { TaskDetailPage } from "../pages/tasks/TaskDetailPage";
import { ObservabilityDashboardPage } from "../pages/observability/ObservabilityDashboardPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Navigate to="/console/traces" replace />
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
