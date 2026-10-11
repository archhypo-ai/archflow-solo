import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Sidebar } from "./components";
import { Chat, type ConversationSummary } from "./features/chat";
import { listConversations } from "./features/chat/api/chatClient";
import { CreateProjectDialog, loadProjects, saveProjects, type Project } from "./features/projects";
import { SettingsDialog } from "./features/settings";
import { LANGUAGE_STORAGE_KEY, toAppLanguage } from "./i18n";
import type { ThemePreference } from "./theme/types";
import "./App.css";

const GLOBAL_AGENT_INSTRUCTIONS_STORAGE_KEY = "archhypo-flow-global-agent-instructions";

function initialGlobalAgentInstructions(): string {
  return localStorage.getItem(GLOBAL_AGENT_INSTRUCTIONS_STORAGE_KEY) ?? "";
}

function newConversationId(): string {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `thread-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function initialTheme(): ThemePreference {
  const storedTheme = localStorage.getItem("archhypo-flow-theme");
  return storedTheme === "day" || storedTheme === "night" || storedTheme === "system"
    ? storedTheme
    : "system";
}

function App() {
  const [theme, setTheme] = useState<ThemePreference>(initialTheme);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
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
    setActiveConversationId(newConversationId());
  }, []);
  const handleConversationUpdated = useCallback(
    (threadId: string, title: string) => {
      setConversations((current) => {
        const existing = current.find((conversation) => conversation.threadId === threadId);
        const updated: ConversationSummary = {
          threadId,
          title,
          messageCount: (existing?.messageCount ?? 0) + 2,
          updatedAt: new Date().toISOString(),
        };
        return [updated, ...current.filter((item) => item.threadId !== threadId)];
      });
    },
    [],
  );
  const handleCreateProject = useCallback((project: Project) => {
    setProjects((current) => [project, ...current]);
  }, []);
  const openCreateProject = useCallback(() => setCreateProjectOpen(true), []);
  const closeCreateProject = useCallback(() => setCreateProjectOpen(false), []);
  const handleConversationSelect = useCallback((threadId: string) => {
    setActiveConversationId(threadId);
  }, []);
  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
    requestAnimationFrame(() => accountTriggerRef.current?.focus());
  }, []);

  useEffect(() => {
    let active = true;
    void listConversations()
      .then((loaded) => {
        if (!active) return;
        const fallbackId = newConversationId();
        setConversations(loaded);
        setActiveConversationId(
          (current) => current ?? loaded[0]?.threadId ?? fallbackId,
        );
      })
      .catch(() => {
        if (!active) return;
        const fallbackId = newConversationId();
        setActiveConversationId((current) => current ?? fallbackId);
      });
    return () => {
      active = false;
    };
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
        activeConversationId={activeConversationId}
        conversations={conversations}
        language={language}
        projects={projects}
        onConversationSelect={handleConversationSelect}
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
        {activeConversationId && (
          <Chat
            key={activeConversationId}
            threadId={activeConversationId}
            language={language}
            onConversationUpdated={handleConversationUpdated}
          />
        )}
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
