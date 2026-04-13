import { ENV_CONFIG } from "./env.config";
import { UI_TEXT } from "../constants/uiText";

export const UI_CONFIG = {
  header: {
    title: UI_TEXT.app.title,
    stage: UI_TEXT.app.stage,
    subtitle: UI_TEXT.app.subtitle,
    searchPlaceholder: UI_TEXT.app.searchPlaceholder,
    environmentLabel: ENV_CONFIG.label,
    showEnvironmentTag: ENV_CONFIG.showEnvironmentTag
  },
  pageShell: {
    showHintBar: true
  }
} as const;
