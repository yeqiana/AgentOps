import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { AlertStat } from "../types/traceConsole";

interface AlertStatsPanelProps {
  stats: AlertStat[];
}

function truncateText(value: string, maxLength = 72) {
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

export function AlertStatsPanel({ stats }: AlertStatsPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.alertStats}</p>
          <h3>{UI_TEXT.panel.alertAggregation}</h3>
        </div>
        <span className="detail-count">{stats.length}</span>
      </div>

      {stats.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noAlertStats}</p>
      ) : (
        <div className="table-scroll observability-table-wrap">
          <table className="trace-table">
            <thead>
              <tr>
                <th>{UI_TEXT.field.severity}</th>
                <th>{UI_TEXT.field.source}</th>
                <th>{UI_TEXT.field.alertCount}</th>
                <th>{UI_TEXT.field.lastCreatedAt}</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((item) => (
                <tr key={`${item.severity}:${item.source_type}`}>
                  <td>
                    <StatusBadge label={alertSeverityLabel(item.severity)} tone={alertTone(item.severity)} />
                  </td>
                  <td title={item.source_type || undefined}>{truncateText(item.source_type, 96)}</td>
                  <td>{item.alert_count}</td>
                  <td>{item.last_created_at || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
