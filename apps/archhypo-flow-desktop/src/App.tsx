import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Sidebar } from "./components";
import { Chat } from "./features/chat";
import { SettingsDialog } from "./features/settings";
import { LANGUAGE_STORAGE_KEY, toAppLanguage } from "./i18n";
import "./App.css";

type Theme = "day" | "night";

function initialTheme(): Theme {
  return localStorage.getItem("archhypo-flow-theme") === "day" ? "day" : "night";
}

function App() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [chatKey, setChatKey] = useState(0);
  const [activeConversationTitle, setActiveConversationTitle] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const accountTriggerRef = useRef<HTMLButtonElement>(null);
  const { t, i18n } = useTranslation();
  const language = toAppLanguage(i18n.resolvedLanguage);

  const handleNewChat = useCallback(() => {
    setActiveConversationTitle("");
    setChatKey((current) => current + 1);
  }, []);
  const handleConversationStarted = useCallback((title: string) => {
    setActiveConversationTitle((current) => current || title);
  }, []);
  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
    requestAnimationFrame(() => accountTriggerRef.current?.focus());
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.lang = language;
    localStorage.setItem("archhypo-flow-theme", theme);
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [theme, language]);

  return (
    <div className="app-shell">
      <Sidebar
        accountTriggerRef={accountTriggerRef}
        activeConversationTitle={activeConversationTitle}
        language={language}
        onNewChat={handleNewChat}
        onLanguageChange={(nextLanguage) =>
          void i18n.changeLanguage(nextLanguage)
        }
        onSettingsOpen={() => setSettingsOpen(true)}
      />
      <main className="main-panel">
        <header className="main-header">
          <div>
            <span className="main-header-eyebrow">{t("app.workspace")}</span>
            <h1>{t("app.chat")}</h1>
          </div>
        </header>
        <Chat
          key={chatKey}
          onConversationStarted={handleConversationStarted}
        />
      </main>
      <SettingsDialog
        open={settingsOpen}
        theme={theme}
        language={language}
        onClose={closeSettings}
        onThemeChange={setTheme}
        onLanguageChange={(nextLanguage) =>
          void i18n.changeLanguage(nextLanguage)
        }
      />
    </div>
  );
}

export default App;
