import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Sidebar } from "../components";
import { Chat } from "../features/chat";
import { useWorkspaceNavigation } from "./hooks/useWorkspaceNavigation";
import {
  DeleteConversationDialog,
  RenameConversationDialog,
  useConversations,
  type ConversationSummary,
} from "../features/conversations";
import {
  CreateProjectDialog,
  DeleteProjectDialog,
  ProjectDetail,
  ProjectIcon,
  RenameProjectDialog,
  useProjects,
  type Project,
} from "../features/projects";
import {
  getGlobalContext,
  saveGlobalContext,
  SettingsDialog,
} from "../features/settings";
import { LANGUAGE_STORAGE_KEY, toAppLanguage } from "../i18n";
import type { ThemePreference } from "../theme/types";
import "./App.css";

function initialTheme(): ThemePreference {
  const storedTheme = localStorage.getItem("archhypo-flow-theme");
  return storedTheme === "day" || storedTheme === "night" || storedTheme === "system"
    ? storedTheme
    : "system";
}

function App() {
  const [theme, setTheme] = useState<ThemePreference>(initialTheme);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [renameTarget, setRenameTarget] = useState<ConversationSummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ConversationSummary | null>(null);
  const [renameProjectTarget, setRenameProjectTarget] = useState<Project | null>(null);
  const [projectSettingsTarget, setProjectSettingsTarget] = useState<Project | null>(null);
  const [deleteProjectTarget, setDeleteProjectTarget] = useState<Project | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [globalContext, setGlobalContext] = useState("");
  const [globalContextLoaded, setGlobalContextLoaded] = useState(false);
  const [globalContextSaving, setGlobalContextSaving] = useState(false);
  const [globalContextLoadError, setGlobalContextLoadError] = useState(false);
  const accountTriggerRef = useRef<HTMLButtonElement>(null);
  const { i18n } = useTranslation();
  const language = toAppLanguage(i18n.resolvedLanguage);

  const conversationStore = useConversations();
  const projectStore = useProjects();
  const navigation = useWorkspaceNavigation({
    conversations: conversationStore.conversations,
    conversationsLoaded: conversationStore.conversationsLoaded,
    projects: projectStore.projects,
  });
  const {
    conversations,
    updateFromChat,
    toggleConversationPin,
    renameConversation,
    deleteConversation,
    removeProjectConversations,
  } = conversationStore;
  const {
    projects,
    createProject,
    updateProjectSettings,
    renameProject,
    deleteProject,
  } = projectStore;
  const {
    activeConversationId,
    activeProjectId,
    pendingProjectId,
    activeConversation,
    chatProject,
    projectLandingProject,
    isProjectLanding,
    isNewConversationActive,
    startNewConversation,
    openProjectHome,
    selectConversation,
    selectConversationAfterUpdate,
    handleConversationDeleted,
    handleProjectDeleted,
  } = navigation;

  const handleConversationUpdated = useCallback(
    (
      threadId: string,
      title: string,
      preview: string,
      projectId: string | null,
    ) => {
      updateFromChat(threadId, title, preview, projectId);
      selectConversationAfterUpdate(threadId);
    },
    [selectConversationAfterUpdate, updateFromChat],
  );
  const openCreateProject = useCallback(() => setCreateProjectOpen(true), []);
  const closeCreateProject = useCallback(() => {
    setCreateProjectOpen(false);
    setProjectSettingsTarget(null);
  }, []);
  const handleSaveConversationTitle = useCallback(
    async (threadId: string, title: string) => {
      await renameConversation(threadId, title);
      setRenameTarget(null);
    },
    [renameConversation],
  );
  const handleConfirmDeleteConversation = useCallback(
    async (threadId: string) => {
      await deleteConversation(threadId);
      handleConversationDeleted(threadId);
      setDeleteTarget(null);
    },
    [deleteConversation, handleConversationDeleted],
  );
  const handleUpdateProjectSettings = useCallback(
    async (project: Project) => {
      await updateProjectSettings(project);
      setProjectSettingsTarget(null);
    },
    [updateProjectSettings],
  );
  const handleRenameProject = useCallback(
    async (projectId: string, name: string) => {
      await renameProject(projectId, name);
      setRenameProjectTarget(null);
    },
    [renameProject],
  );
  const handleConfirmDeleteProject = useCallback(
    async (projectId: string) => {
      await deleteProject(projectId);
      removeProjectConversations(projectId);
      handleProjectDeleted(projectId);
      setDeleteProjectTarget(null);
    },
    [deleteProject, handleProjectDeleted, removeProjectConversations],
  );
  const handleSaveGlobalContext = useCallback(async (context: string) => {
    setGlobalContextSaving(true);
    try {
      const saved = await saveGlobalContext(context);
      setGlobalContext(saved);
      setGlobalContextLoadError(false);
    } finally {
      setGlobalContextSaving(false);
    }
  }, []);
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
    let cancelled = false;

    const loadGlobalContext = async () => {
      try {
        const saved = await getGlobalContext();
        if (cancelled) return;
        setGlobalContext(saved);
        setGlobalContextLoadError(false);
      } catch {
        if (!cancelled) setGlobalContextLoadError(true);
      } finally {
        if (!cancelled) setGlobalContextLoaded(true);
      }
    };

    void loadGlobalContext();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className={`app-shell${sidebarCollapsed ? " is-sidebar-collapsed" : ""}`}>
      <Sidebar
        accountTriggerRef={accountTriggerRef}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((collapsed) => !collapsed)}
        activeConversationId={activeConversationId}
        activeProjectId={activeProjectId}
        isNewConversationActive={isNewConversationActive}
        conversations={conversations}
        language={language}
        projects={projects}
        onConversationSelect={selectConversation}
        onProjectSelect={openProjectHome}
        onRenameProject={setRenameProjectTarget}
        onEditProjectSettings={setProjectSettingsTarget}
        onDeleteProject={setDeleteProjectTarget}
        onRenameConversation={setRenameTarget}
        onToggleConversationPin={toggleConversationPin}
        onDeleteConversation={setDeleteTarget}
        onNewChat={startNewConversation}
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
                    onClick={() => openProjectHome(chatProject.id)}
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
                  onSelectConversation={selectConversation}
                  onRenameConversation={setRenameTarget}
                  onToggleConversationPin={toggleConversationPin}
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
        onCreate={createProject}
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
        globalContext={globalContext}
        globalContextLoading={!globalContextLoaded}
        globalContextSaving={globalContextSaving}
        globalContextLoadError={globalContextLoadError}
        onClose={closeSettings}
        onThemeChange={setTheme}
        onLanguageChange={(nextLanguage) =>
          void i18n.changeLanguage(nextLanguage)
        }
        onGlobalContextSave={handleSaveGlobalContext}
      />
    </div>
  );
}

export default App;
