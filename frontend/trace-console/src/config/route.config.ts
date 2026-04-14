import { UI_TEXT } from "../constants/uiText";

export const ROUTE_PATHS = {
  login: "/login",
  root: "/",
  console: "/console",
  observability: "/console/observability",
  alerts: "/console/alerts",
  traces: "/console/traces",
  traceDetail: "/console/traces/:traceId",
  taskDetail: "/console/tasks/:taskId"
} as const;

export const DEFAULT_CONSOLE_ROUTE = ROUTE_PATHS.observability;

interface BreadcrumbRule {
  test: (pathname: string) => boolean;
  labels: string[];
}

const BREADCRUMB_RULES: BreadcrumbRule[] = [
  {
    test: (pathname) => pathname.includes("/console/traces/"),
    labels: [UI_TEXT.nav.running, UI_TEXT.nav.traces, UI_TEXT.nav.traceDetail]
  },
  {
    test: (pathname) => pathname.includes("/console/tasks/"),
    labels: [UI_TEXT.nav.running, UI_TEXT.nav.taskManagement, UI_TEXT.nav.taskDetail]
  },
  {
    test: (pathname) => pathname.includes("/console/alerts"),
    labels: [UI_TEXT.nav.running, UI_TEXT.nav.alertCenter]
  },
  {
    test: (pathname) => pathname.includes("/console/traces"),
    labels: [UI_TEXT.nav.running, UI_TEXT.nav.traces]
  },
  {
    test: (pathname) => pathname.includes("/console/observability"),
    labels: [UI_TEXT.nav.observability]
  }
];

export function getBreadcrumbLabels(pathname: string): string[] {
  return BREADCRUMB_RULES.find((rule) => rule.test(pathname))?.labels ?? [UI_TEXT.nav.observability];
}
