import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Sidebar } from "./components";
import { Chat, type ConversationSummary } from "./features/chat";
import {
  deleteConversation as deleteConversationApi,
  listConversations,
  updateConversation as updateConversationApi,
} from "./features/chat/api/chatClient";
import {
  DeleteConversationDialog,
  RenameConversationDialog,
} from "./features/conversations/ConversationDialogs";
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

function sortConversations(conversations: ConversationSummary[]): ConversationSummary[] {
  return [...conversations].sort((left, right) => {
    if (left.pinned !== right.pinned) return left.pinned ? -1 : 1;
    return right.updatedAt.localeCompare(left.updatedAt);
  });
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
  const [renameTarget, setRenameTarget] = useState<ConversationSummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ConversationSummary | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>(loadProjects);
  const [globalAgentInstructions, setGlobalAgentInstructions] = useState(
    initialGlobalAgentInstructions,
  );
  const accountTriggerRef = useRef<HTMLButtonElement>(null);
  const { i18n } = useTranslation();
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
          pinned: existing?.pinned ?? false,
        };
        return sortConversations([
          updated,
          ...current.filter((item) => item.threadId !== threadId),
        ]);
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
  const handleToggleConversationPin = useCallback(
    async (conversation: ConversationSummary) => {
      try {
        const updated = await updateConversationApi(conversation.threadId, {
          pinned: !conversation.pinned,
        });
        setConversations((current) =>
          sortConversations([
            updated,
            ...current.filter((item) => item.threadId !== updated.threadId),
          ]),
        );
      } catch (error) {
        console.error("Could not update conversation pin state", error);
      }
    },
    [],
  );
  const handleSaveConversationTitle = useCallback(
    async (threadId: string, title: string) => {
      const updated = await updateConversationApi(threadId, { title });
      setConversations((current) =>
        sortConversations([
          updated,
          ...current.filter((item) => item.threadId !== updated.threadId),
        ]),
      );
      setRenameTarget(null);
    },
    [],
  );
  const handleConfirmDeleteConversation = useCallback(
    async (threadId: string) => {
      await deleteConversationApi(threadId);
      setConversations((current) =>
        current.filter((conversation) => conversation.threadId !== threadId),
      );
      setActiveConversationId((current) =>
        current === threadId ? newConversationId() : current,
      );
      setDeleteTarget(null);
    },
    [],
  );
  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
    requestAnimationFrame(() => accountTriggerRef.current?.focus());
  }, []);

  const activeConversation = conversations.find(
    (conversation) => conversation.threadId === activeConversationId,
  );
  const isNewConversationActive = Boolean(activeConversationId && !activeConversation);

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
        isNewConversationActive={isNewConversationActive}
        conversations={conversations}
        language={language}
        projects={projects}
        onConversationSelect={handleConversationSelect}
        onRenameConversation={setRenameTarget}
        onToggleConversationPin={(conversation) =>
          void handleToggleConversationPin(conversation)
        }
        onDeleteConversation={setDeleteTarget}
        onNewChat={handleNewChat}
        onNewProject={openCreateProject}
        onLanguageChange={(nextLanguage) =>
          void i18n.changeLanguage(nextLanguage)
        }
        onSettingsOpen={() => setSettingsOpen(true)}
      />
      <main className="main-panel">
        <header className="main-header">
          {activeConversation && (
            <div className="main-header-breadcrumb">
              {/* A project icon and name can be inserted before the conversation title. */}
              <h1 title={activeConversation.title}>{activeConversation.title}</h1>
            </div>
          )}
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
      <RenameConversationDialog
        conversation={renameTarget}
        onClose={() => setRenameTarget(null)}
        onSave={handleSaveConversationTitle}
      />
      <DeleteConversationDialog
        conversation={deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDeleteConversation}
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
