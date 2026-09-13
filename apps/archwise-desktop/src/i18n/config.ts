import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import english from "./locales/en.json";
import portuguese from "./locales/pt-BR.json";

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: english },
    "pt-BR": { translation: portuguese },
  },
  lng: "en",
  fallbackLng: "en",
  supportedLngs: ["en", "pt-BR"],
  interpolation: { escapeValue: false },
  react: { useSuspense: false },
});

export default i18n;
