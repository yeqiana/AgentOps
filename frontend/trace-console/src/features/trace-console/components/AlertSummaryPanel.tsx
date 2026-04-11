import { Link } from "react-router-dom";
import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { OperationsRecentAlert } from "../types/traceConsole";

interface AlertSummaryPanelProps {
  alerts: OperationsRecentAlert[];
}

function truncateText(value: string, maxLength = 120) {
  if (!value) {
    return "-";
  }
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function alertTone(severity: string): "neutral" | "warning" | "error" {
  if (severity === "critical" || severity === "error") {
    return "error";
  }
  if (severity) {
    return "warning";
  }
  return "neutral";
}

function alertSeverityLabel(severity: string): string {
  return UI_TEXT.statusLabel[severity as keyof typeof UI_TEXT.statusLabel] || severity || "-";
}

export function AlertSummaryPanel({ alerts }: AlertSummaryPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.alertSummary}</p>
          <h3>{UI_TEXT.panel.recentAlerts}</h3>
        </div>
        <span className="detail-count">{alerts.length}</span>
      </div>

      {alerts.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noRecentAlerts}</p>
      ) : (
        <div className="observability-list">
          {alerts.map((alert) => (
            <article className="observability-list-card" key={alert.id}>
              <div className="detail-panel-header">
                <div>
                  <h4>{truncateText(alert.event_code, 72)}</h4>
                  <p className="muted-text">
                    {alert.source_type || "-"} / {truncateText(alert.source_name, 48)} / {alert.created_at || "-"}
                  </p>
                </div>
                <StatusBadge label={alertSeverityLabel(alert.severity)} tone={alertTone(alert.severity)} />
              </div>
              <p className="long-text-block line-clamp-3">{truncateText(alert.message)}</p>
              <details className="long-text-details">
                <summary>{UI_TEXT.action.viewFullContent}</summary>
                <p className="long-text-block">{alert.message || "-"}</p>
              </details>
              {alert.trace_id ? (
                <div className="panel-actions">
                  <Link className="button" to={`/console/traces/${encodeURIComponent(alert.trace_id)}`}>
                    {UI_TEXT.action.openTraceDetail}
                  </Link>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
