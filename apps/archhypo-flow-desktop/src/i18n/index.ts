import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import ptBR from "./locales/pt-BR.json";

export type AppLanguage = "en" | "pt-BR";
const LANGUAGE_STORAGE_KEY = "archhypo-flow-language";

export function toAppLanguage(language?: string): AppLanguage {
  return language?.toLowerCase().startsWith("en") ? "en" : "pt-BR";
}

function initialLanguage(): AppLanguage {
  const saved = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (saved === "en" || saved === "pt-BR") return saved;
  return toAppLanguage(navigator.language);
}

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    "pt-BR": { translation: ptBR },
  },
  lng: initialLanguage(),
  fallbackLng: "pt-BR",
  supportedLngs: ["en", "pt-BR"],
  interpolation: { escapeValue: false },
});

export { LANGUAGE_STORAGE_KEY };
export default i18n;
