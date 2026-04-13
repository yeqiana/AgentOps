import { Link } from "react-router-dom";
import { UI_TEXT } from "../../../constants/uiText";
import type { OperationsRouteStat } from "../types/traceConsole";

interface RouteStatsPanelProps {
  stats: OperationsRouteStat[];
}

function truncateText(value: string, maxLength = 72) {
  if (!value) {
    return "-";
  }
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

export function RouteStatsPanel({ stats }: RouteStatsPanelProps) {
  return (
    <section className="panel detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="detail-panel-kicker">{UI_TEXT.panel.routeStats}</p>
          <h3>{UI_TEXT.panel.routingDecisions}</h3>
        </div>
        <span className="detail-count">{stats.length}</span>
      </div>

      {stats.length === 0 ? (
        <p className="muted-text">{UI_TEXT.state.noRouteStats}</p>
      ) : (
        <>
          <p className="panel-hint">{UI_TEXT.state.staleTraceReferenceHint}</p>
          <div className="table-scroll observability-table-wrap">
            <table className="trace-table">
              <thead>
                <tr>
                  <th>{UI_TEXT.field.route}</th>
                  <th>{UI_TEXT.field.source}</th>
                  <th>{UI_TEXT.field.decisions}</th>
                  <th>{UI_TEXT.field.lastTask}</th>
                  <th>{UI_TEXT.field.lastTrace}</th>
                  <th>{UI_TEXT.field.lastDecidedAt}</th>
                </tr>
              </thead>
              <tbody>
                {stats.map((item) => (
                  <tr key={`${item.route_name}:${item.route_source}`}>
                    <td>{truncateText(item.route_name)}</td>
                    <td>{item.route_source || "-"}</td>
                    <td>{item.decision_count}</td>
                    <td>
                      {item.last_task_id ? (
                        <Link className="trace-link" to={`/console/tasks/${encodeURIComponent(item.last_task_id)}`}>
                          {truncateText(item.last_task_id, 48)}
                        </Link>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>
                      {item.last_trace_id ? (
                        <Link className="trace-link" to={`/console/traces/${encodeURIComponent(item.last_trace_id)}`}>
                          {truncateText(item.last_trace_id, 48)}
                        </Link>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>{item.last_decided_at || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
