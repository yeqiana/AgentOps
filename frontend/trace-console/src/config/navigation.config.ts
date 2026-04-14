import { UI_TEXT } from "../constants/uiText";
import { PERMISSIONS } from "../features/auth/permissions";
import { ROUTE_PATHS } from "./route.config";

export interface NavigationItem {
  label: string;
  to: string;
  badge?: string;
  disabled?: boolean;
  permissionCodes?: string[];
}

export interface NavigationSection {
  title: string;
  items: NavigationItem[];
}

export const NAVIGATION_SECTIONS: NavigationSection[] = [
  {
    title: UI_TEXT.nav.overview,
    items: [{ label: UI_TEXT.nav.observability, to: ROUTE_PATHS.observability, permissionCodes: [PERMISSIONS.taskRead] }]
  },
  {
    title: UI_TEXT.nav.running,
    items: [
      { label: UI_TEXT.nav.traces, to: ROUTE_PATHS.traces, badge: "链路", permissionCodes: [PERMISSIONS.traceRead] },
      { label: UI_TEXT.nav.taskManagement, to: ROUTE_PATHS.observability, badge: "任务", permissionCodes: [PERMISSIONS.taskRead] },
      { label: UI_TEXT.nav.alertCenter, to: ROUTE_PATHS.alerts, permissionCodes: [PERMISSIONS.alertRead] }
    ]
  },
  {
    title: UI_TEXT.nav.capability,
    items: [
      { label: UI_TEXT.nav.agents, to: ROUTE_PATHS.observability, disabled: true },
      { label: UI_TEXT.nav.tools, to: ROUTE_PATHS.observability, disabled: true },
      { label: UI_TEXT.nav.modelsAndRouting, to: ROUTE_PATHS.observability, disabled: true }
    ]
  },
  {
    title: UI_TEXT.nav.settings,
    items: [
      { label: UI_TEXT.nav.permissions, to: ROUTE_PATHS.observability, disabled: true },
      { label: UI_TEXT.nav.auditLogs, to: ROUTE_PATHS.observability, disabled: true }
    ]
  }
];
