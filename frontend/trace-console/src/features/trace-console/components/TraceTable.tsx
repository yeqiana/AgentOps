import { Link } from 'react-router-dom';
import { StatusBadge } from '../../../components/StatusBadge';
import { UI_CONFIG } from '../../../config/ui.config';
import { UI_TEXT } from '../../../constants/uiText';
import type { ConsoleTraceListItem } from '../types/traceConsole';

interface TraceTableProps {
  items: ConsoleTraceListItem[];
}

function getStatusTone(statusCode: number): 'success' | 'warning' | 'error' {
  if (statusCode >= 500) return 'error';
  if (statusCode >= 400) return 'warning';
  return 'success';
}

function getReviewTone(reviewStatus: string): 'neutral' | 'success' | 'warning' | 'error' {
  if (reviewStatus === 'pass') return 'success';
  if (reviewStatus === 'fail') return 'error';
  if (reviewStatus) return 'warning';
  return 'neutral';
}

function getReviewLabel(reviewStatus: string): string {
  if (reviewStatus === 'pass') return UI_TEXT.status.pass;
  if (reviewStatus === 'fail') return UI_TEXT.status.fail;
  return reviewStatus || '-';
}

function Truncate({ text, className = '' }: { text: string; className?: string }) {
  return (
    <span className={`truncate-one-line ${className}`.trim()} title={text}>
      {text}
    </span>
  );
}

export function TraceTable({ items }: TraceTableProps) {
  const widths = UI_CONFIG.traceTable.columns;

  return (
    <section className="panel table-panel">
      <div className="table-panel-header">
        <div>
          <p className="toolbar-kicker">结果列表</p>
          <h3>按固定列宽展示请求链路</h3>
        </div>
        <span className="detail-count">{items.length}</span>
      </div>
      <div className="table-scroll">
        <table className="trace-table trace-table-admin">
          <colgroup>
            <col style={{ width: widths.trace }} />
            <col style={{ width: widths.methodPath }} />
            <col style={{ width: widths.status }} />
            <col style={{ width: widths.startTime }} />
            <col style={{ width: widths.task }} />
            <col style={{ width: widths.route }} />
            <col style={{ width: widths.execution }} />
            <col style={{ width: widths.review }} />
            <col style={{ width: widths.alert }} />
          </colgroup>
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
                  <Link className="trace-link truncate-one-line" title={item.trace_id} to={`/console/traces/${item.trace_id}`}>
                    {item.trace_id}
                  </Link>
                  <div className="muted-text truncate-one-line" title={item.request_id || '-'}>{item.request_id || '-'}</div>
                </td>
                <td>
                  <div className="table-method-row"><span className="table-method-chip">{item.method}</span></div>
                  <div className="muted-text"><Truncate text={item.path} /></div>
                </td>
                <td>
                  <StatusBadge label={String(item.status_code)} tone={getStatusTone(item.status_code)} />
                  <div className="muted-text truncate-one-line" title={item.error_code || (item.rate_limited ? UI_TEXT.status.rateLimited : '-')}>
                    {item.error_code || (item.rate_limited ? UI_TEXT.status.rateLimited : '-')}
                  </div>
                </td>
                <td>
                  <div className="truncate-one-line" title={item.started_at}>{item.started_at}</div>
                  <div className="muted-text truncate-one-line" title={item.updated_at}>{item.updated_at}</div>
                </td>
                <td><Truncate text={item.task_id || '-'} /></td>
                <td>
                  <div><Truncate text={item.route_name || '-'} /></div>
                  <div className="muted-text"><Truncate text={item.route_source || '-'} /></div>
                </td>
                <td><Truncate text={item.execution_mode || '-'} /></td>
                <td><StatusBadge label={getReviewLabel(item.review_status)} tone={getReviewTone(item.review_status)} /></td>
                <td>{item.alert_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
