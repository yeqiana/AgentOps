import { getJson } from "../../../lib/http/client";
import type {
  ConsoleTraceListResponse,
  OperationsOverviewResponse,
  TaskSummaryResponse,
  TraceConsoleViewerResponse,
  TraceListFilters
} from "../types/traceConsole";

export interface TraceListRequest extends TraceListFilters {
  page: number;
  page_size: number;
}

export function getConsoleTraces(params: TraceListRequest) {
  return getJson<ConsoleTraceListResponse>("/console/traces", { ...params });
}

export function getTraceConsoleViewer(traceId: string) {
  return getJson<TraceConsoleViewerResponse>(`/console/traces/${encodeURIComponent(traceId)}/viewer`);
}

export function getTaskSummary(taskId: string) {
  return getJson<TaskSummaryResponse>(`/tasks/${encodeURIComponent(taskId)}/summary`);
}

export function getOperationsOverview() {
  return getJson<OperationsOverviewResponse>("/operations/overview");
}
