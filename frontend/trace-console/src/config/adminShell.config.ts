export const ADMIN_SHELL_CONFIG = {
  shell: {
    contentMaxWidth: 1680,
    contentPaddingX: 24,
    contentPaddingY: 18,
    sidebarWidth: 256,
    headerHeight: 72,
    footerCompact: true
  },
  density: {
    tableRowHeight: 60,
    toolbarControlHeight: 38,
    cardMinHeight: 168,
    kpiCardMinHeight: 132,
    moduleCardMinHeight: 168,
    detailPanelMinHeight: 240
  },
  typography: {
    pageTitle: 30,
    sectionTitle: 18,
    body: 14,
    meta: 12
  },
  traceTable: {
    columns: {
      trace: 220,
      methodPath: 240,
      status: 120,
      startTime: 180,
      task: 180,
      route: 190,
      execution: 120,
      review: 120,
      alert: 84
    }
  },
  pageKickers: {
    dashboard: '运行总览',
    traceList: '请求链路检索',
    traceDetail: '请求链路诊断',
    taskDetail: '任务视图'
  }
} as const;
