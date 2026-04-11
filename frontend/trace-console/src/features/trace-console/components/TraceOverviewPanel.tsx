import { StatusBadge } from "../../../components/StatusBadge";
import { LinkButton } from "../../../components/LinkButton";
import { UI_TEXT } from "../../../constants/uiText";
import type { TraceConsoleViewer } from "../types/traceConsole";

interface TraceOverviewPanelProps {
  viewer: TraceConsoleViewer;
}

function statusTone(statusCode: number): "success" | "warning" | "error" {
  if (statusCode >= 500) {
    return "error";
  }
  if (statusCode >= 400) {
    return "warning";
  }
  return "success";
}

function reviewTone(reviewStatus: string): "neutral" | "success" | "warning" | "error" {
  if (reviewStatus === "pass") {
    return "success";
  }
  if (reviewStatus === "fail") {
    return "error";
  }
  return reviewStatus ? "warning" : "neutral";
}

function reviewLabel(reviewStatus: string): string {
  if (reviewStatus === "pass") {
    return UI_TEXT.status.pass;
  }
  if (reviewStatus === "fail") {
    return UI_TEXT.status.fail;
  }
  return reviewStatus || "-";
}

function displayValue(value: string | number | boolean): string {
  if (typeof value === "boolean") {
    return value ? UI_TEXT.common.yes : UI_TEXT.common.no;
  }
  return String(value || "-");
}

function KeyValue({ label, value }: { label: string; value: string | number | boolean }) {
  return (
    <div className="detail-kv-item">
      <dt>{label}</dt>
      <dd>{displayValue(value)}</dd>
    </div>
  );
}

export function TraceOverviewPanel({ viewer }: TraceOverviewPanelProps) {
  const { trace } = viewer;
  const task = viewer.summary.task;

  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.overview}</p>
          <h3>{UI_TEXT.panel.traceOverview}</h3>
        </div>
        <StatusBadge label={String(trace.status_code)} tone={statusTone(trace.status_code)} />
      </div>

      <dl className="detail-kv-grid">
        <KeyValue label={UI_TEXT.field.traceId} value={trace.trace_id} />
        <KeyValue label={UI_TEXT.field.requestId} value={trace.request_id} />
        <KeyValue label={UI_TEXT.field.method} value={trace.method} />
        <KeyValue label={UI_TEXT.field.path} value={trace.path} />
        <KeyValue label={UI_TEXT.field.errorCode} value={trace.error_code} />
        <KeyValue label={UI_TEXT.field.rateLimited} value={trace.rate_limited} />
        <KeyValue label={UI_TEXT.field.startTime} value={trace.started_at} />
        <KeyValue label={UI_TEXT.field.updateTime} value={trace.updated_at} />
      </dl>

      <div className="linked-task-card">
        <div className="detail-panel-header">
          <div>
            <p className="detail-panel-kicker">{UI_TEXT.panel.linkedTask}</p>
            <h3>{task?.id || UI_TEXT.panel.noLinkedTask}</h3>
          </div>
          {task ? <StatusBadge label={reviewLabel(task.review_status)} tone={reviewTone(task.review_status)} /> : null}
        </div>
        {task ? (
          <>
            <dl className="detail-kv-grid compact">
              <KeyValue label={UI_TEXT.field.status} value={task.status} />
              <KeyValue label={UI_TEXT.field.route} value={task.route_name} />
              <KeyValue label={UI_TEXT.field.executionMode} value={task.execution_mode} />
              <KeyValue label={UI_TEXT.field.reviewStatus} value={reviewLabel(task.review_status)} />
            </dl>
            <div className="panel-actions">
              <LinkButton to={`/console/tasks/${encodeURIComponent(task.id)}`}>{UI_TEXT.action.openTaskDetail}</LinkButton>
            </div>
          </>
        ) : (
          <p className="muted-text">{UI_TEXT.state.noLinkedTaskSummary}</p>
        )}
      </div>
    </section>
  );
}
