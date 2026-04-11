import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { TraceAlert } from "../types/traceConsole";

interface TraceAlertsPanelProps {
  alerts: TraceAlert[];
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
  if (severity === "critical") {
    return UI_TEXT.status.critical;
  }
  if (severity === "error") {
    return UI_TEXT.status.error;
  }
  if (severity === "warning") {
    return UI_TEXT.status.warning;
  }
  return severity || "-";
}

export function TraceAlertsPanel({ alerts }: TraceAlertsPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.alerts}</p>
          <h3>{UI_TEXT.panel.alertEvents}</h3>
        </div>
        <span className="detail-count">{alerts.length}</span>
      </div>

      {alerts.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noAlerts}</p>
      ) : (
        <div className="alert-list">
          {alerts.map((alert) => (
            <article className="alert-card" key={alert.id}>
              <div className="detail-panel-header">
                <div>
                  <h4>{alert.event_code}</h4>
                  <p className="muted-text">
                    {alert.source_type} / {alert.source_name} · {alert.created_at}
                  </p>
                </div>
                <StatusBadge label={alertSeverityLabel(alert.severity)} tone={alertTone(alert.severity)} />
              </div>
              <p className="long-text-block line-clamp-3">{alert.message || "-"}</p>
              <details className="long-text-details">
                <summary>{UI_TEXT.action.viewFullContent}</summary>
                <p className="long-text-block">{alert.message || "-"}</p>
              </details>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
