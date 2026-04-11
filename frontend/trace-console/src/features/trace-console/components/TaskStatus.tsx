import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { TaskPayload } from "../types/traceConsole";

interface TaskStatusProps {
  task: TaskPayload;
}

function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

function getStatusTone(status: string): "neutral" | "success" | "warning" | "error" {
  const normalizedStatus = status.toLowerCase();
  if (["completed", "success", "succeeded", "done"].includes(normalizedStatus)) {
    return "success";
  }
  if (["failed", "error", "cancelled"].includes(normalizedStatus)) {
    return "error";
  }
  if (status) {
    return "warning";
  }
  return "neutral";
}

function getReviewTone(reviewStatus: string): "neutral" | "success" | "warning" | "error" {
  if (reviewStatus === "pass") {
    return "success";
  }
  if (reviewStatus === "fail") {
    return "error";
  }
  if (reviewStatus) {
    return "warning";
  }
  return "neutral";
}

function statusLabel(status: string): string {
  return UI_TEXT.statusLabel[status as keyof typeof UI_TEXT.statusLabel] || status || "-";
}

function KeyValue({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="detail-kv-item">
      <dt>{label}</dt>
      <dd>{displayValue(value)}</dd>
    </div>
  );
}

export function TaskStatus({ task }: TaskStatusProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.status}</p>
          <h3>{UI_TEXT.panel.taskStatus}</h3>
        </div>
        <StatusBadge label={statusLabel(task.status)} tone={getStatusTone(task.status)} />
      </div>

      <dl className="detail-kv-grid">
        <KeyValue label={UI_TEXT.field.executionMode} value={task.execution_mode} />
        <KeyValue label={UI_TEXT.field.routeName} value={task.route_name} />
        <KeyValue label={UI_TEXT.field.routeSource} value={task.route_source} />
        <div className="detail-kv-item">
          <dt>{UI_TEXT.field.reviewStatus}</dt>
          <dd>
            <StatusBadge label={statusLabel(task.review_status)} tone={getReviewTone(task.review_status)} />
          </dd>
        </div>
        <KeyValue label={UI_TEXT.field.toolCount} value={task.tool_count} />
        <KeyValue label={UI_TEXT.field.errorMessage} value={task.error_message} />
      </dl>
    </section>
  );
}
