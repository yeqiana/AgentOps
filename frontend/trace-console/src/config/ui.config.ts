import { ENV_CONFIG } from './env.config';
import { UI_TEXT } from '../constants/uiText';
import { ADMIN_SHELL_CONFIG } from './adminShell.config';

export const UI_CONFIG = {
  header: {
    title: UI_TEXT.app.title,
    stage: UI_TEXT.app.stage,
    subtitle: UI_TEXT.app.subtitle,
    searchPlaceholder: UI_TEXT.app.searchPlaceholder,
    environmentLabel: ENV_CONFIG.label,
    showEnvironmentTag: ENV_CONFIG.showEnvironmentTag,
    primaryActionLabel: '新建任务',
    secondaryActionLabel: '刷新'
  },
  pageShell: {
    showHintBar: true,
    maxWidth: ADMIN_SHELL_CONFIG.shell.contentMaxWidth,
    paddingX: ADMIN_SHELL_CONFIG.shell.contentPaddingX,
    paddingY: ADMIN_SHELL_CONFIG.shell.contentPaddingY,
    pageKickers: ADMIN_SHELL_CONFIG.pageKickers
  },
  density: ADMIN_SHELL_CONFIG.density,
  typography: ADMIN_SHELL_CONFIG.typography,
  traceTable: ADMIN_SHELL_CONFIG.traceTable
} as const;
