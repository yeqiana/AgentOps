import { useEffect, useState } from 'react';
import { PageStateView } from '../../components/PageStateView';
import { UI_CONFIG } from '../../config/ui.config';
import { UI_TEXT } from '../../constants/uiText';
import { getConsoleTraces } from '../../features/trace-console/api/traceConsoleApi';
import { TraceFilterBar } from '../../features/trace-console/components/TraceFilterBar';
import { TracePagination } from '../../features/trace-console/components/TracePagination';
import { TraceTable } from '../../features/trace-console/components/TraceTable';
import type { ConsoleTraceListResponse, TraceListFilters } from '../../features/trace-console/types/traceConsole';
import { ListPageShell } from '../../layouts/ListPageShell';
import { HttpError } from '../../lib/http/client';

const defaultFilters: TraceListFilters = {
  trace_id: '',
  task_id: '',
  path: '',
  method: '',
  status_code: '',
  route_name: ''
};

const pageSize = 20;

export function TraceListPage() {
  const [filters, setFilters] = useState<TraceListFilters>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState<TraceListFilters>(defaultFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ConsoleTraceListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noPermission, setNoPermission] = useState(false);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      setNoPermission(false);

      try {
        const response = await getConsoleTraces({
          ...appliedFilters,
          page,
          page_size: pageSize
        });
        if (!active) return;
        setData(response);
      } catch (caught) {
        if (!active) return;
        setData(null);
        if (caught instanceof HttpError && (caught.status === 401 || caught.status === 403)) {
          setNoPermission(true);
          return;
        }
        setError(UI_TEXT.state.traceListLoadFailed);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [appliedFilters, page]);

  function handleSearch() {
    setAppliedFilters({ ...filters });
    setPage(1);
  }

  function handleReset() {
    setFilters({ ...defaultFilters });
    setAppliedFilters({ ...defaultFilters });
    setPage(1);
  }

  const hasFilters = Object.values(appliedFilters).some((value) => String(value).trim() !== '');
  const filtersSlot = (
    <TraceFilterBar filters={filters} onChange={setFilters} onSubmit={handleSearch} onReset={handleReset} disabled={loading} />
  );
  const paginationSlot = !loading && !noPermission && !error && data && data.items.length > 0 ? (
    <TracePagination page={data.page} pageSize={data.page_size} total={data.total} hasNext={data.has_next} onPageChange={setPage} />
  ) : null;

  return (
    <ListPageShell
      title={UI_TEXT.page.traceListTitle}
      subtitle="固定列宽、高密度表格、统一筛选工具栏，用于后台请求链路检索与问题初筛。"
      hint={UI_TEXT.hint.traceList}
      filters={filtersSlot}
      pagination={paginationSlot}
      kicker={UI_CONFIG.pageShell.pageKickers.traceList}
    >
      {loading ? <PageStateView title={UI_TEXT.common.loading} description={UI_TEXT.state.loadingTraceList} /> : null}
      {!loading && noPermission ? <PageStateView title={UI_TEXT.common.noPermission} description={UI_TEXT.state.traceListNoPermission} /> : null}
      {!loading && !noPermission && error ? (
        <PageStateView
          title={UI_TEXT.common.loadFailed}
          description={error}
          actions={
            <button className="button button-primary" type="button" onClick={() => setAppliedFilters((current) => ({ ...current }))}>
              {UI_TEXT.action.retry}
            </button>
          }
        />
      ) : null}
      {!loading && !noPermission && !error && data && data.items.length === 0 ? (
        <PageStateView
          title={hasFilters ? UI_TEXT.common.noResults : UI_TEXT.state.noTraces}
          description={hasFilters ? UI_TEXT.state.adjustFilters : UI_TEXT.state.noTraceRecords}
        />
      ) : null}
      {!loading && !noPermission && !error && data && data.items.length > 0 ? <TraceTable items={data.items} /> : null}
    </ListPageShell>
  );
}
