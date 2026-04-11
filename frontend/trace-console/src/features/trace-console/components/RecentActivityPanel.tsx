import { Link } from "react-router-dom";
import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { OperationsRecentTask } from "../types/traceConsole";

interface RecentActivityPanelProps {
  tasks: OperationsRecentTask[];
}

function truncateText(value: string, maxLength = 72) {
  if (!value) {
    return "-";
  }
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function statusTone(status: string): "neutral" | "success" | "warning" | "error" {
  if (status === "completed" || status === "succeeded" || status === "success") {
    return "success";
  }
  if (status === "failed" || status === "error" || status === "cancelled") {
    return "error";
  }
  if (status) {
    return "warning";
  }
  return "neutral";
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

function statusLabel(status: string): string {
  return UI_TEXT.statusLabel[status as keyof typeof UI_TEXT.statusLabel] || status || "-";
}

export function RecentActivityPanel({ tasks }: RecentActivityPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.recentActivity}</p>
          <h3>{UI_TEXT.panel.recentTasks}</h3>
        </div>
        <span className="detail-count">{tasks.length}</span>
      </div>

      {tasks.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noRecentTasks}</p>
      ) : (
        <div className="observability-list">
          {tasks.map((task) => (
            <article className="observability-list-card" key={task.id}>
              <div className="detail-panel-header">
                <div>
                  <h4>
                    <Link className="trace-link" to={`/console/tasks/${encodeURIComponent(task.id)}`}>
                      {truncateText(task.id, 64)}
                    </Link>
                  </h4>
                  <p className="muted-text">
                    {truncateText(task.route_name, 48)} / {task.route_source || "-"} / {task.updated_at || "-"}
                  </p>
                </div>
                <StatusBadge label={statusLabel(task.status)} tone={statusTone(task.status)} />
              </div>
              <div className="panel-actions">
                {task.trace_id ? (
                  <Link className="button" to={`/console/traces/${encodeURIComponent(task.trace_id)}`}>
                    {UI_TEXT.action.openTraceDetail}
                  </Link>
                ) : null}
                <StatusBadge label={statusLabel(task.review_status)} tone={reviewTone(task.review_status)} />
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
