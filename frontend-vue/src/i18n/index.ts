import { createI18n } from "vue-i18n";
import { messages, type AppLocale } from "./messages";

export const defaultLocale: AppLocale = "zh-CN";

export const i18n = createI18n({
  fallbackLocale: "en",
  legacy: false,
  locale: defaultLocale,
  messages
});
