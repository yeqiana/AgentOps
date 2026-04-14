import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PageStateView } from "../../components/PageStateView";
import { getAlerts } from "../../features/trace-console/api/traceConsoleApi";
import { AlertFilterBar } from "../../features/trace-console/components/AlertFilterBar";
import { AlertPagination } from "../../features/trace-console/components/AlertPagination";
import { AlertTable } from "../../features/trace-console/components/AlertTable";
import type { AlertListFilters, AlertListResponse } from "../../features/trace-console/types/traceConsole";
import { ListPageShell } from "../../layouts/ListPageShell";
import { HttpError } from "../../lib/http/client";

const defaultFilters: AlertListFilters = {
  severity: "",
  source_type: "",
  trace_id: ""
};

const pageSize = 20;

function readFiltersFromQuery(searchParams: URLSearchParams): AlertListFilters {
  return {
    severity: searchParams.get("severity") ?? "",
    source_type: searchParams.get("source_type") ?? "",
    trace_id: searchParams.get("trace_id") ?? ""
  };
}

function writeFiltersToQuery(filters: AlertListFilters, setSearchParams: ReturnType<typeof useSearchParams>[1]) {
  const next = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value.trim()) {
      next.set(key, value.trim());
    }
  }
  setSearchParams(next, { replace: true });
}

export function AlertCenterPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryString = searchParams.toString();
  const queryFilters = useMemo(() => readFiltersFromQuery(searchParams), [queryString]);
  const [filters, setFilters] = useState<AlertListFilters>(queryFilters);
  const [appliedFilters, setAppliedFilters] = useState<AlertListFilters>(queryFilters);
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<AlertListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noPermission, setNoPermission] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    setFilters(queryFilters);
    setAppliedFilters(queryFilters);
    setOffset(0);
  }, [queryFilters]);

  useEffect(() => {
    let active = true;

    async function loadAlerts() {
      setLoading(true);
      setError(null);
      setNoPermission(false);

      try {
        const response = await getAlerts({
          ...appliedFilters,
          limit: pageSize,
          offset
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
        setError("加载失败，请重试");
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadAlerts();

    return () => {
      active = false;
    };
  }, [appliedFilters, offset, retryKey]);

  function handleSearch() {
    const next = { ...filters };
    setAppliedFilters(next);
    setOffset(0);
    writeFiltersToQuery(next, setSearchParams);
  }

  function handleReset() {
    setFilters({ ...defaultFilters });
    setAppliedFilters({ ...defaultFilters });
    setOffset(0);
    setSearchParams(new URLSearchParams(), { replace: true });
  }

  const items = data?.alerts ?? [];
  const hasFilters = Object.values(appliedFilters).some((value) => value.trim() !== "");
  const filtersSlot = <AlertFilterBar filters={filters} onChange={setFilters} onSubmit={handleSearch} onReset={handleReset} disabled={loading} />;
  const paginationSlot = !loading && !noPermission && !error && data && items.length > 0 ? (
    <AlertPagination limit={pageSize} offset={offset} itemCount={items.length} onPageChange={setOffset} />
  ) : null;

  return (
    <ListPageShell
      title="告警中心"
      subtitle="告警列表、基础筛选与关联请求链路跳转"
      hint="支持按严重级别、来源类型和请求链路 ID 筛选；无请求链路 ID 的告警不会生成跳转链接。"
      filters={filtersSlot}
      pagination={paginationSlot}
      kicker="告警中心"
    >
      {loading ? <PageStateView title="正在加载..." description="正在加载..." /> : null}
      {!loading && noPermission ? <PageStateView title="当前账号无权访问该页面" description="当前账号无权访问该页面" /> : null}
      {!loading && !noPermission && error ? (
        <PageStateView
          title="加载失败，请重试"
          description={error}
          actions={
            <button className="button button-primary" type="button" onClick={() => setRetryKey((current) => current + 1)}>
              重试
            </button>
          }
        />
      ) : null}
      {!loading && !noPermission && !error && items.length === 0 ? (
        <PageStateView title={hasFilters ? "无匹配结果" : "暂无告警"} description={hasFilters ? "当前筛选条件下没有匹配告警。" : "当前暂无可展示的告警。"} />
      ) : null}
      {!loading && !noPermission && !error && items.length > 0 ? <AlertTable items={items} /> : null}
    </ListPageShell>
  );
}
