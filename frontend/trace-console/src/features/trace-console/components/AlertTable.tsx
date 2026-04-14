import { Link } from "react-router-dom";
import { StatusBadge } from "../../../components/StatusBadge";
import type { AlertListItem } from "../types/traceConsole";

interface AlertTableProps {
  items: AlertListItem[];
}

function displayValue(value: string | null | undefined, fallback = "-") {
  return value && value.trim() ? value : fallback;
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

function Truncate({ text, className = "" }: { text: string; className?: string }) {
  return (
    <span className={`truncate-one-line ${className}`.trim()} title={text}>
      {text}
    </span>
  );
}

export function AlertTable({ items }: AlertTableProps) {
  return (
    <section className="panel table-panel">
      <div className="table-panel-header">
        <div>
          <p className="toolbar-kicker">结果列表</p>
          <h3>按创建时间倒序展示告警</h3>
        </div>
        <span className="detail-count">{items.length}</span>
      </div>
      <div className="table-scroll">
        <table className="trace-table trace-table-admin">
          <colgroup>
            <col style={{ width: 220 }} />
            <col style={{ width: 120 }} />
            <col style={{ width: 150 }} />
            <col style={{ width: 180 }} />
            <col style={{ width: 160 }} />
            <col style={{ width: 320 }} />
            <col style={{ width: 240 }} />
            <col style={{ width: 180 }} />
            <col style={{ width: 140 }} />
          </colgroup>
          <thead>
            <tr>
              <th>告警 ID</th>
              <th>严重级别</th>
              <th>来源类型</th>
              <th>来源名称</th>
              <th>事件编码</th>
              <th>消息</th>
              <th>请求链路 ID</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => {
              const traceId = displayValue(item.trace_id, "");
              const alertId = displayValue(item.id, "-");
              return (
                <tr key={`${alertId}-${item.created_at || index}`}>
                  <td>
                    <Truncate text={alertId} />
                  </td>
                  <td>
                    <StatusBadge label={displayValue(item.severity, "未知")} tone={alertTone(item.severity)} />
                  </td>
                  <td>
                    <Truncate text={displayValue(item.source_type, "未知")} />
                  </td>
                  <td>
                    <Truncate text={displayValue(item.source_name)} />
                  </td>
                  <td>
                    <Truncate text={displayValue(item.event_code)} />
                  </td>
                  <td>
                    <Truncate text={displayValue(item.message, "无告警描述")} />
                  </td>
                  <td>
                    {traceId ? (
                      <Link className="trace-link truncate-one-line" title={traceId} to={`/console/traces/${encodeURIComponent(traceId)}`}>
                        {traceId}
                      </Link>
                    ) : (
                      <span className="muted-text" title="该告警未关联请求链路">
                        未关联请求链路
                      </span>
                    )}
                  </td>
                  <td>
                    <Truncate text={displayValue(item.created_at)} />
                  </td>
                  <td>
                    {traceId ? (
                      <Link className="button" to={`/console/traces/${encodeURIComponent(traceId)}`}>
                        查看请求链路
                      </Link>
                    ) : (
                      <button className="button" type="button" disabled title="该告警未关联请求链路">
                        查看请求链路
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
