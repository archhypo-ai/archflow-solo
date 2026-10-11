import type { Language } from "../../i18n/types";

export type AppearancePreference = "dark" | "light" | "system";
export type SettingsSectionId = "general" | "agent";

export const APP_SETTING_KEYS = {
  appearance: "appearance",
  language: "language",
} as const;

export type AppSettingKey =
  (typeof APP_SETTING_KEYS)[keyof typeof APP_SETTING_KEYS];

export type AppSettingValues = {
  [APP_SETTING_KEYS.appearance]: AppearancePreference;
  [APP_SETTING_KEYS.language]: Language;
};

export const DEFAULT_APP_SETTINGS: Readonly<AppSettingValues> = {
  appearance: "system",
  language: "en",
};
