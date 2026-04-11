import { Link } from "react-router-dom";
import { StatusBadge } from "../../../components/StatusBadge";
import { UI_TEXT } from "../../../constants/uiText";
import type { ConsoleTraceListItem } from "../types/traceConsole";

interface TraceTableProps {
  items: ConsoleTraceListItem[];
}

function getStatusTone(statusCode: number): "success" | "warning" | "error" {
  if (statusCode >= 500) {
    return "error";
  }
  if (statusCode >= 400) {
    return "warning";
  }
  return "success";
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

function getReviewLabel(reviewStatus: string): string {
  if (reviewStatus === "pass") {
    return UI_TEXT.status.pass;
  }
  if (reviewStatus === "fail") {
    return UI_TEXT.status.fail;
  }
  return reviewStatus || "-";
}

export function TraceTable({ items }: TraceTableProps) {
  return (
    <section className="panel table-panel">
      <div className="table-scroll">
        <table className="trace-table">
          <thead>
            <tr>
              <th>{UI_TEXT.field.trace}</th>
              <th>{UI_TEXT.field.methodPath}</th>
              <th>{UI_TEXT.field.status}</th>
              <th>{UI_TEXT.field.startTime}</th>
              <th>{UI_TEXT.field.task}</th>
              <th>{UI_TEXT.field.route}</th>
              <th>{UI_TEXT.field.execution}</th>
              <th>{UI_TEXT.field.review}</th>
              <th>{UI_TEXT.field.alert}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.trace_id}>
                <td>
                  <Link className="trace-link" to={`/console/traces/${item.trace_id}`}>
                    {item.trace_id}
                  </Link>
                  <div className="muted-text">{item.request_id || "-"}</div>
                </td>
                <td>
                  <div>{item.method}</div>
                  <div className="muted-text">{item.path}</div>
                </td>
                <td>
                  <StatusBadge label={String(item.status_code)} tone={getStatusTone(item.status_code)} />
                  <div className="muted-text">{item.error_code || (item.rate_limited ? UI_TEXT.status.rateLimited : "-")}</div>
                </td>
                <td>
                  <div>{item.started_at}</div>
                  <div className="muted-text">{item.updated_at}</div>
                </td>
                <td>{item.task_id || "-"}</td>
                <td>
                  <div>{item.route_name || "-"}</div>
                  <div className="muted-text">{item.route_source || "-"}</div>
                </td>
                <td>{item.execution_mode || "-"}</td>
                <td>
                  <StatusBadge label={getReviewLabel(item.review_status)} tone={getReviewTone(item.review_status)} />
                </td>
                <td>{item.alert_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
