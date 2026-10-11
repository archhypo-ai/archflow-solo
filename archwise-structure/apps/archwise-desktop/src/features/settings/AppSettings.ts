import {
  APP_SETTING_KEYS,
  DEFAULT_APP_SETTINGS,
  type AppSettingKey,
  type AppSettingValues,
  type AppearancePreference,
} from "./types";

const STORAGE_KEY = "archwise.app-settings.v1";
type StoredAppSettings = Partial<AppSettingValues>;

function readSettings(): StoredAppSettings {
  if (typeof window === "undefined") return {};

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? (parsed as StoredAppSettings)
      : {};
  } catch {
    return {};
  }
}

function writeSettings(settings: StoredAppSettings) {
  if (typeof window === "undefined") return;

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Preferences are optional and must not prevent the shell from starting.
  }
}

function isAppearance(value: unknown): value is AppearancePreference {
  return value === "dark" || value === "light" || value === "system";
}

function isLanguage(value: unknown): value is AppSettingValues["language"] {
  return value === "en" || value === "pt-BR";
}

export const AppSettings = {
  async get<K extends AppSettingKey>(
    key: K,
  ): Promise<AppSettingValues[K] | undefined> {
    const value = readSettings()[key];
    if (key === APP_SETTING_KEYS.appearance && isAppearance(value)) {
      return value as AppSettingValues[K];
    }
    if (key === APP_SETTING_KEYS.language && isLanguage(value)) {
      return value as AppSettingValues[K];
    }
    return undefined;
  },

  async getOrDefault<K extends AppSettingKey>(
    key: K,
  ): Promise<AppSettingValues[K]> {
    return (await AppSettings.get(key)) ?? DEFAULT_APP_SETTINGS[key];
  },

  async set<K extends AppSettingKey>(
    key: K,
    value: AppSettingValues[K],
  ): Promise<void> {
    const settings = readSettings();
    settings[key] = value;
    writeSettings(settings);
  },
};
