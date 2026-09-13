import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      chat: {
        inputPlaceholder: "Ask ArchWISE anything...",
        message: "Message",
        addAttachment: "Add attachment",
        send: "Send message",
        validationDisclaimer: "ArchWISE is a research prototype. Validate generated decisions.",
      },
    },
  },
};

void i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  react: { useSuspense: false },
});

export default i18n;
