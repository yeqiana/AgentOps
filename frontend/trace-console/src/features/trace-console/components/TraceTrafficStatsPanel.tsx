import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { TraceStat } from "../types/traceConsole";

interface TraceTrafficStatsPanelProps {
  stats: TraceStat[];
}

function truncateText(value: string, maxLength = 72) {
  if (!value) {
    return "-";
  }
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function statusTone(statusCode: number, rateLimited: boolean): "neutral" | "success" | "warning" | "error" {
  if (rateLimited) {
    return "warning";
  }
  if (statusCode >= 400) {
    return "error";
  }
  if (statusCode >= 200 && statusCode < 400) {
    return "success";
  }
  return "neutral";
}

export function TraceTrafficStatsPanel({ stats }: TraceTrafficStatsPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.traceTrafficStats}</p>
          <h3>{UI_TEXT.panel.traceTraffic}</h3>
        </div>
        <span className="detail-count">{stats.length}</span>
      </div>

      {stats.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noTraceStats}</p>
      ) : (
        <div className="table-scroll observability-table-wrap">
          <table className="trace-table">
            <thead>
              <tr>
                <th>{UI_TEXT.field.method}</th>
                <th>{UI_TEXT.field.path}</th>
                <th>{UI_TEXT.field.statusCode}</th>
                <th>{UI_TEXT.field.rateLimited}</th>
                <th>{UI_TEXT.field.traceCount}</th>
                <th>{UI_TEXT.field.lastStartedAt}</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((item) => (
                <tr key={`${item.method}:${item.path}:${item.status_code}:${item.rate_limited}`}>
                  <td>{item.method || "-"}</td>
                  <td title={item.path || undefined}>{truncateText(item.path, 96)}</td>
                  <td>
                    <StatusBadge label={String(item.status_code || "-")} tone={statusTone(item.status_code, item.rate_limited)} />
                  </td>
                  <td>
                    <StatusBadge
                      label={item.rate_limited ? UI_TEXT.common.yes : UI_TEXT.common.no}
                      tone={item.rate_limited ? "warning" : "neutral"}
                    />
                  </td>
                  <td>{item.trace_count}</td>
                  <td>{item.last_started_at || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
