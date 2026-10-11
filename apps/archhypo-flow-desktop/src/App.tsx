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
import {
  CreateProjectDialog,
  createProject as createProjectApi,
  DeleteProjectDialog,
  deleteProject as deleteProjectApi,
  listProjects,
  loadProjects,
  renameProject as renameProjectApi,
  updateProjectSettings as updateProjectSettingsApi,
  RenameProjectDialog,
  saveProjects,
  ProjectDetail,
  ProjectIcon,
  type Project,
} from "./features/projects";
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
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [pendingProjectId, setPendingProjectId] = useState<string | null>(null);
  const [renameTarget, setRenameTarget] = useState<ConversationSummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ConversationSummary | null>(null);
  const [renameProjectTarget, setRenameProjectTarget] = useState<Project | null>(null);
  const [projectSettingsTarget, setProjectSettingsTarget] = useState<Project | null>(null);
  const [deleteProjectTarget, setDeleteProjectTarget] = useState<Project | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>(loadProjects);
  const [globalAgentInstructions, setGlobalAgentInstructions] = useState(
    initialGlobalAgentInstructions,
  );
  const accountTriggerRef = useRef<HTMLButtonElement>(null);
  const { i18n } = useTranslation();
  const language = toAppLanguage(i18n.resolvedLanguage);
  const activeConversation = conversations.find(
    (conversation) => conversation.threadId === activeConversationId,
  );
  const activeProject = projects.find((project) => project.id === activeProjectId);
  const activeConversationProject = projects.find(
    (project) => project.id === activeConversation?.projectId,
  );
  const chatProject =
    activeConversationProject ??
    projects.find((project) => project.id === pendingProjectId);
  const projectLandingProject =
    activeProject ?? (!activeConversation ? chatProject : undefined);
  const isProjectLanding = Boolean(
    activeConversationId && projectLandingProject && !activeConversation,
  );
  const isNewConversationActive = Boolean(
    activeConversationId && !activeConversation && !projectLandingProject,
  );

  const handleNewChat = useCallback(() => {
    setActiveProjectId(null);
    setPendingProjectId(null);
    setActiveConversationId(newConversationId());
  }, []);
  const handleProjectSelect = useCallback((projectId: string) => {
    setActiveConversationId(newConversationId());
    setPendingProjectId(projectId);
    setActiveProjectId(projectId);
  }, []);
  const handleConversationUpdated = useCallback(
    (
      threadId: string,
      title: string,
      preview: string,
      projectId: string | null,
    ) => {
      setConversations((current) => {
        const existing = current.find((conversation) => conversation.threadId === threadId);
        const updated: ConversationSummary = {
          threadId,
          title,
          messageCount: (existing?.messageCount ?? 0) + 2,
          updatedAt: new Date().toISOString(),
          pinned: existing?.pinned ?? false,
          projectId: projectId ?? existing?.projectId ?? null,
          preview,
        };
        return sortConversations([
          updated,
          ...current.filter((item) => item.threadId !== threadId),
        ]);
      });
      setActiveConversationId(threadId);
      setActiveProjectId(null);
      setPendingProjectId(null);
    },
    [],
  );
  const handleCreateProject = useCallback(async (project: Project) => {
    const savedProject = await createProjectApi(project);
    setProjects((current) => [
      savedProject,
      ...current.filter((item) => item.id !== savedProject.id),
    ]);
  }, []);
  const openCreateProject = useCallback(() => setCreateProjectOpen(true), []);
  const closeCreateProject = useCallback(() => {
    setCreateProjectOpen(false);
    setProjectSettingsTarget(null);
  }, []);
  const handleConversationSelect = useCallback(
    (threadId: string) => {
      const selected = conversations.find((conversation) => conversation.threadId === threadId);
      setActiveProjectId(null);
      setPendingProjectId(selected?.projectId ?? null);
      setActiveConversationId(threadId);
    },
    [conversations],
  );
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
  const handleUpdateProjectSettings = useCallback(async (project: Project) => {
    const updated = await updateProjectSettingsApi(project);
    setProjects((current) =>
      current.map((item) => (item.id === updated.id ? updated : item)),
    );
    setProjectSettingsTarget(null);
  }, []);
  const handleRenameProject = useCallback(
    async (projectId: string, name: string) => {
      const renamed = await renameProjectApi(projectId, name);
      setProjects((current) =>
        current.map((project) => (project.id === projectId ? renamed : project)),
      );
      setRenameProjectTarget(null);
    },
    [],
  );
  const handleConfirmDeleteProject = useCallback(
    async (projectId: string) => {
      await deleteProjectApi(projectId);
      setProjects((current) => current.filter((project) => project.id !== projectId));
      setConversations((current) =>
        current.filter((conversation) => conversation.projectId !== projectId),
      );
      setActiveProjectId((current) => (current === projectId ? null : current));
      if (
        activeProjectId === projectId ||
        activeConversation?.projectId === projectId ||
        pendingProjectId === projectId
      ) {
        setActiveConversationId(newConversationId());
      }
      if (pendingProjectId === projectId) setPendingProjectId(null);
      setDeleteProjectTarget(null);
    },
    [activeConversation?.projectId, activeProjectId, pendingProjectId],
  );
  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
    requestAnimationFrame(() => accountTriggerRef.current?.focus());
  }, []);

  useEffect(() => {
    let active = true;
    void listProjects()
      .then(async (storedProjects) => {
        if (!active) return;
        if (storedProjects.length > 0) {
          setProjects(storedProjects);
          return;
        }

        const importedProjects: Project[] = [];
        for (const project of loadProjects()) {
          try {
            importedProjects.push(await createProjectApi(project));
          } catch (error) {
            console.error("Could not import a locally stored project", error);
          }
        }
        if (active) setProjects(importedProjects);
      })
      .catch((error: unknown) => {
        console.error("Could not load projects from the local API", error);
      });
    return () => {
      active = false;
    };
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
        activeProjectId={activeProjectId}
        isNewConversationActive={isNewConversationActive}
        conversations={conversations}
        language={language}
        projects={projects}
        onConversationSelect={handleConversationSelect}
        onProjectSelect={handleProjectSelect}
        onRenameProject={setRenameProjectTarget}
        onEditProjectSettings={setProjectSettingsTarget}
        onDeleteProject={setDeleteProjectTarget}
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
              {chatProject && (
                <>
                  <button
                    className="main-header-project-link"
                    type="button"
                    onClick={() => handleProjectSelect(chatProject.id)}
                    title={chatProject.name}
                  >
                    <ProjectIcon icon={chatProject.icon} color={chatProject.color} size={17} />
                    <span>{chatProject.name}</span>
                  </button>
                  <span className="main-header-separator" aria-hidden="true">/</span>
                </>
              )}
              <h1 title={activeConversation.title}>{activeConversation.title}</h1>
            </div>
          )}
        </header>
        {activeConversationId && (
          <Chat
            key={activeConversationId}
            threadId={activeConversationId}
            language={language}
            projectId={activeConversation?.projectId ?? pendingProjectId}
            project={projectLandingProject ?? chatProject ?? null}
            projectLanding={isProjectLanding}
            projectLandingContent={
              projectLandingProject ? (
                <ProjectDetail
                  conversations={conversations
                    .filter((conversation) => conversation.projectId === projectLandingProject.id)
                    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))}
                  language={language}
                  onSelectConversation={handleConversationSelect}
                  onRenameConversation={setRenameTarget}
                  onToggleConversationPin={(conversation) =>
                    void handleToggleConversationPin(conversation)
                  }
                  onDeleteConversation={setDeleteTarget}
                />
              ) : undefined
            }
            onConversationUpdated={handleConversationUpdated}
          />
        )}
      </main>
      <CreateProjectDialog
        open={createProjectOpen || projectSettingsTarget !== null}
        project={projectSettingsTarget}
        onClose={closeCreateProject}
        onCreate={handleCreateProject}
        onUpdate={handleUpdateProjectSettings}
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
      <RenameProjectDialog
        project={renameProjectTarget}
        onClose={() => setRenameProjectTarget(null)}
        onSave={handleRenameProject}
      />
      <DeleteProjectDialog
        project={deleteProjectTarget}
        conversationCount={deleteProjectTarget
          ? conversations.filter((conversation) => conversation.projectId === deleteProjectTarget.id).length
          : 0}
        onClose={() => setDeleteProjectTarget(null)}
        onConfirm={handleConfirmDeleteProject}
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
