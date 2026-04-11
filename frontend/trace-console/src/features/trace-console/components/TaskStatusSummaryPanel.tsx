import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { OperationsTaskStatusStat } from "../types/traceConsole";

interface TaskStatusSummaryPanelProps {
  stats: OperationsTaskStatusStat[];
}

function statusTone(status: string): "neutral" | "success" | "warning" | "error" {
  if (status === "completed" || status === "succeeded" || status === "success") {
    return "success";
  }
  if (status === "failed" || status === "error" || status === "cancelled") {
    return "error";
  }
  if (status === "running" || status === "pending" || status === "retrying") {
    return "warning";
  }
  return "neutral";
}

function statusLabel(status: string): string {
  return UI_TEXT.statusLabel[status as keyof typeof UI_TEXT.statusLabel] || status || "-";
}

export function TaskStatusSummaryPanel({ stats }: TaskStatusSummaryPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.taskStatus}</p>
          <h3>{UI_TEXT.panel.statusSummary}</h3>
        </div>
        <span className="detail-count">{stats.length}</span>
      </div>

      {stats.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noTaskStatusStats}</p>
      ) : (
        <div className="detail-kv-grid">
          {stats.map((item) => (
            <div className="detail-kv-item" key={item.status || "unknown"}>
              <dt>
                <StatusBadge label={statusLabel(item.status)} tone={statusTone(item.status)} />
              </dt>
              <dd>{item.task_count}</dd>
              <p className="muted-text">
                {UI_TEXT.field.lastUpdatedAt}：{item.last_updated_at || "-"}
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
