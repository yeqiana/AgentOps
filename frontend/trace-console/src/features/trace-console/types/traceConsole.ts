export interface ConsoleTraceListItem {
  trace_id: string;
  request_id: string;
  method: string;
  path: string;
  status_code: number;
  error_code: string;
  rate_limited: boolean;
  started_at: string;
  updated_at: string;
  session_id: string;
  turn_id: string;
  task_id: string;
  route_name: string;
  route_source: string;
  execution_mode: string;
  review_status: string;
  alert_count: number;
  last_event_at: string;
}

export interface ConsoleTraceListResponse {
  items: ConsoleTraceListItem[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
}

export interface TraceListFilters {
  trace_id: string;
  task_id: string;
  path: string;
  method: string;
  status_code: string;
  route_name: string;
}

export interface TracePayload {
  trace_id: string;
  request_id: string;
  method: string;
  path: string;
  status_code: number;
  error_code: string;
  rate_limited: boolean;
  started_at: string;
  updated_at: string;
}

export interface LinkedTaskPayload {
  id: string;
  status: string;
  route_name: string;
  execution_mode: string;
  review_status: string;
}

export interface TraceTimelineEvent {
  happened_at: string;
  event_type: string;
  source_type: string;
  source_name: string;
  title: string;
  details: string;
}

export interface TraceTaskEvent {
  id: string;
  event_type: string;
  event_message: string;
  event_payload_json: string;
  created_at: string;
}

export interface TraceToolResult {
  id: string;
  tool_name: string;
  success: boolean;
  exit_code: number;
  stdout: string;
  stderr: string;
  created_at: string;
}

export interface TraceAlert {
  id: string;
  severity: string;
  source_type: string;
  source_name: string;
  event_code: string;
  message: string;
  created_at: string;
}

export interface TraceGraphNode {
  node_id: string;
  node_type: string;
  title: string;
  subtitle: string;
  happened_at: string;
}

export interface TraceGraphEdge {
  source_id: string;
  target_id: string;
  edge_type: string;
}

export interface TraceConsoleViewer {
  trace: TracePayload;
  summary: {
    task: LinkedTaskPayload | null;
    task_events: TraceTaskEvent[];
    tool_results: TraceToolResult[];
  };
  timeline: TraceTimelineEvent[];
  graph_nodes: TraceGraphNode[];
  graph_edges: TraceGraphEdge[];
  alerts: TraceAlert[];
}

export interface TraceConsoleViewerResponse {
  viewer: TraceConsoleViewer;
}

export interface TaskPayload {
  id: string;
  trace_id: string;
  status: string;
  session_id: string;
  turn_id: string;
  execution_mode: string;
  route_name: string;
  route_source: string;
  review_status: string;
  tool_count: number;
  error_message: string;
  user_input: string;
  answer: string;
  created_at: string;
  updated_at: string;
}

export interface TaskRelatedTracePayload {
  trace_id: string;
  method: string;
  path: string;
  status_code: number;
}

export interface TaskSummary {
  task: TaskPayload | null;
  trace: TaskRelatedTracePayload | null;
  task_events: TraceTaskEvent[];
  tool_results: TraceToolResult[];
  route_decisions: unknown[];
  alerts: TraceAlert[];
}

export interface TaskSummaryResponse {
  summary: TaskSummary;
}

export interface OperationsRuntimeSummary {
  max_workers: number;
  active_task_count: number;
  active_task_ids: string[];
}

export interface OperationsTaskStatusStat {
  status: string;
  task_count: number;
  last_updated_at: string;
}

export interface OperationsRecentTask {
  id: string;
  trace_id: string;
  status: string;
  route_name: string;
  route_source: string;
  review_status: string;
  updated_at: string;
}

export interface OperationsRouteStat {
  route_name: string;
  route_source: string;
  decision_count: number;
  last_trace_id: string;
  last_task_id: string;
  last_decided_at: string;
}

export interface OperationsRecentAlert {
  id: string;
  trace_id: string;
  source_type: string;
  source_name: string;
  severity: string;
  event_code: string;
  message: string;
  created_at: string;
}

export interface OperationsOverviewSummary {
  runtime: OperationsRuntimeSummary;
  task_stats: OperationsTaskStatusStat[];
  recent_tasks: OperationsRecentTask[];
  route_stats: OperationsRouteStat[];
  recent_alerts: OperationsRecentAlert[];
}

export interface OperationsOverviewResponse {
  summary: OperationsOverviewSummary;
}

export interface TraceStat {
  method: string;
  path: string;
  status_code: number;
  rate_limited: boolean;
  trace_count: number;
  last_started_at: string;
}

export interface TraceStatsResponse {
  stats: TraceStat[];
}

export interface AlertStat {
  severity: string;
  source_type: string;
  alert_count: number;
  last_created_at: string;
}

export interface AlertStatsResponse {
  stats: AlertStat[];
}
