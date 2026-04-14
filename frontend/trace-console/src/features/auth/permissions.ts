export const PERMISSIONS = {
  traceRead: "trace.read",
  taskRead: "task.read",
  alertRead: "alert.read"
} as const;

export const ROUTE_PERMISSION_MAP = [
  { pathPrefix: "/console/observability", permission: PERMISSIONS.taskRead },
  { pathPrefix: "/console/alerts", permission: PERMISSIONS.alertRead },
  { pathPrefix: "/console/traces", permission: PERMISSIONS.traceRead },
  { pathPrefix: "/console/tasks", permission: PERMISSIONS.taskRead }
] as const;
