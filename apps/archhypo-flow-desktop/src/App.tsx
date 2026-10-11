import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Sidebar } from "./components";
import { Chat } from "./features/chat";
import { CreateProjectDialog, loadProjects, saveProjects, type Project } from "./features/projects";
import { SettingsDialog } from "./features/settings";
import { LANGUAGE_STORAGE_KEY, toAppLanguage } from "./i18n";
import type { ThemePreference } from "./theme/types";
import "./App.css";

const GLOBAL_AGENT_INSTRUCTIONS_STORAGE_KEY = "archhypo-flow-global-agent-instructions";

function initialGlobalAgentInstructions(): string {
  return localStorage.getItem(GLOBAL_AGENT_INSTRUCTIONS_STORAGE_KEY) ?? "";
}

function initialTheme(): ThemePreference {
  const storedTheme = localStorage.getItem("archhypo-flow-theme");
  return storedTheme === "day" || storedTheme === "night" || storedTheme === "system"
    ? storedTheme
    : "system";
}

function App() {
  const [theme, setTheme] = useState<ThemePreference>(initialTheme);
  const [chatKey, setChatKey] = useState(0);
  const [activeConversationTitle, setActiveConversationTitle] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>(loadProjects);
  const [globalAgentInstructions, setGlobalAgentInstructions] = useState(
    initialGlobalAgentInstructions,
  );
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
  const handleCreateProject = useCallback((project: Project) => {
    setProjects((current) => [project, ...current]);
  }, []);
  const openCreateProject = useCallback(() => setCreateProjectOpen(true), []);
  const closeCreateProject = useCallback(() => setCreateProjectOpen(false), []);
  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
    requestAnimationFrame(() => accountTriggerRef.current?.focus());
  }, []);

  useEffect(() => {
    const systemTheme = window.matchMedia("(prefers-color-scheme: light)");
    const applyTheme = () => {
      document.documentElement.dataset.theme =
        theme === "system" ? (systemTheme.matches ? "day" : "night") : theme;
    };

    applyTheme();
    systemTheme.addEventListener("change", applyTheme);
    return () => systemTheme.removeEventListener("change", applyTheme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = language;
    localStorage.setItem("archhypo-flow-theme", theme);
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  }, [theme, language]);

  useEffect(() => {
    saveProjects(projects);
  }, [projects]);

  useEffect(() => {
    localStorage.setItem(
      GLOBAL_AGENT_INSTRUCTIONS_STORAGE_KEY,
      globalAgentInstructions,
    );
  }, [globalAgentInstructions]);

  return (
    <div className="app-shell">
      <Sidebar
        accountTriggerRef={accountTriggerRef}
        activeConversationTitle={activeConversationTitle}
        language={language}
        projects={projects}
        onNewChat={handleNewChat}
        onNewProject={openCreateProject}
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
      <CreateProjectDialog
        open={createProjectOpen}
        onClose={closeCreateProject}
        onCreate={handleCreateProject}
      />
      <SettingsDialog
        open={settingsOpen}
        theme={theme}
        language={language}
        globalAgentInstructions={globalAgentInstructions}
        onClose={closeSettings}
        onThemeChange={setTheme}
        onLanguageChange={(nextLanguage) =>
          void i18n.changeLanguage(nextLanguage)
        }
        onGlobalAgentInstructionsChange={setGlobalAgentInstructions}
      />
    </div>
  );
}

export default App;
