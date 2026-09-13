import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";
import { I18nextProvider, useTranslation } from "react-i18next";
import { AppSettings } from "../features/settings/AppSettings";
import type { Language } from "./types";
import i18n from "./config";

type I18nContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: PropsWithChildren) {
  const [language, setLanguageState] = useState<Language>("en");
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    void AppSettings.getOrDefault("language").then((stored) => {
      if (!active) return;
      setLanguageState(stored);
      setSettingsLoaded(true);
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    void i18n.changeLanguage(language);
    if (settingsLoaded) void AppSettings.set("language", language);
  }, [language, settingsLoaded]);

  const setLanguage = useCallback((nextLanguage: Language) => {
    setLanguageState(nextLanguage);
  }, []);

  const value = useMemo(
    () => ({ language, setLanguage }),
    [language, setLanguage],
  );

  return (
    <I18nextProvider i18n={i18n}>
      <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
    </I18nextProvider>
  );
}

export function useI18n() {
  const translation = useTranslation();
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");

  return { ...translation, ...context };
}
