import { useCallback, useEffect, useRef, useState } from "react";
import { Layers } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Sidebar } from "../components";
import { ArtifactDetailPage, ArtifactsPage } from "../features/artifacts";
import type { ArtifactSummary } from "../features/artifacts/types";
import { Chat } from "../features/chat";
import { ReviewCardsPreviewDialog } from "../features/chat/components/ReviewCardsPreviewDialog";
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
  useProjects,
  type Project,
} from "../features/projects";
import {
  getGlobalContext,
  getHitlEnabled,
  saveGlobalContext,
  saveHitlEnabled,
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
  const [hitlEnabled, setHitlEnabled] = useState(getHitlEnabled);
  const [hitlSaveError, setHitlSaveError] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [artifactsLibraryOpen, setArtifactsLibraryOpen] = useState(false);
  const [activeArtifact, setActiveArtifact] = useState<ArtifactSummary | null>(null);
  const [renameTarget, setRenameTarget] = useState<ConversationSummary | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ConversationSummary | null>(null);
  const [projectSettingsTarget, setProjectSettingsTarget] = useState<Project | null>(null);
  const [deleteProjectTarget, setDeleteProjectTarget] = useState<Project | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [reviewCardsPreviewOpen, setReviewCardsPreviewOpen] = useState(false);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [globalContext, setGlobalContext] = useState("");
  const [globalContextLoaded, setGlobalContextLoaded] = useState(false);
  const [globalContextSaving, setGlobalContextSaving] = useState(false);
  const [globalContextLoadError, setGlobalContextLoadError] = useState(false);
  const accountTriggerRef = useRef<HTMLButtonElement>(null);
  const { i18n, t } = useTranslation();
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
    handleConversationDeleted,
    handleProjectDeleted,
  } = navigation;

  const handleConversationStarted = useCallback(
    (
      threadId: string,
      title: string,
      userMessage: string,
      projectId: string | null,
    ) => {
      updateFromChat(threadId, title, userMessage, projectId, 1);
    },
    [updateFromChat],
  );
  const handleConversationUpdated = useCallback(
    (
      threadId: string,
      title: string,
      preview: string,
      projectId: string | null,
    ) => {
      updateFromChat(threadId, title, preview, projectId, 1);
    },
    [updateFromChat],
  );
  const closeReviewCardsPreview = useCallback(
    () => setReviewCardsPreviewOpen(false),
    [],
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
  const handleHitlChange = useCallback((enabled: boolean) => {
    try {
      saveHitlEnabled(enabled);
      setHitlEnabled(enabled);
      setHitlSaveError(false);
    } catch {
      setHitlSaveError(true);
    }
  }, []);
  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
    requestAnimationFrame(() => accountTriggerRef.current?.focus());
  }, []);
  const handleNewConversation = useCallback(() => {
    setArtifactsLibraryOpen(false);
    setActiveArtifact(null);
    startNewConversation();
  }, [startNewConversation]);
  const handleProjectSelect = useCallback(
    (projectId: string) => {
      setArtifactsLibraryOpen(false);
      setActiveArtifact(null);
      openProjectHome(projectId);
    },
    [openProjectHome],
  );
  const handleConversationSelect = useCallback(
    (threadId: string) => {
      setArtifactsLibraryOpen(false);
      setActiveArtifact(null);
      selectConversation(threadId);
    },
    [selectConversation],
  );
  const handleArtifactSelect = useCallback((artifact: ArtifactSummary) => {
    setArtifactsLibraryOpen(false);
    setActiveArtifact(artifact);
  }, []);
  const handleArtifactsSelect = useCallback(() => {
    setActiveArtifact(null);
    setArtifactsLibraryOpen(true);
  }, []);
  const handleReturnToArtifacts = useCallback(() => {
    setActiveArtifact(null);
    setArtifactsLibraryOpen(true);
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
        activeConversationId={
          artifactsLibraryOpen || activeArtifact ? null : activeConversationId
        }
        activeProjectId={artifactsLibraryOpen || activeArtifact ? null : activeProjectId}
        isNewConversationActive={
          !artifactsLibraryOpen && !activeArtifact && isNewConversationActive
        }
        isArtifactsActive={artifactsLibraryOpen || activeArtifact !== null}
        conversations={conversations}
        language={language}
        projects={projects}
        onConversationSelect={handleConversationSelect}
        onProjectSelect={handleProjectSelect}
        onEditProjectSettings={setProjectSettingsTarget}
        onDeleteProject={setDeleteProjectTarget}
        onRenameConversation={setRenameTarget}
        onToggleConversationPin={toggleConversationPin}
        onDeleteConversation={setDeleteTarget}
        onNewChat={handleNewConversation}
        onArtifactsSelect={handleArtifactsSelect}
        onNewProject={openCreateProject}
        onLanguageChange={(nextLanguage) =>
          void i18n.changeLanguage(nextLanguage)
        }
        onSettingsOpen={() => setSettingsOpen(true)}
        onLogoutClick={() => setReviewCardsPreviewOpen(true)}
      />
      <main className="main-panel">
        <header className="main-header">
          {activeArtifact ? (
            <div className="main-header-breadcrumb">
              <button
                className="main-header-project-link"
                type="button"
                onClick={handleReturnToArtifacts}
                title={t("artifacts.pageTitle")}
              >
                <Layers size={17} aria-hidden="true" />
                <span>{t("artifacts.pageTitle")}</span>
              </button>
              <span className="main-header-separator" aria-hidden="true">
                /
              </span>
              <h1 title={activeArtifact.title}>{activeArtifact.title}</h1>
            </div>
          ) : artifactsLibraryOpen ? (
            <div className="main-header-breadcrumb">
              <Layers size={17} aria-hidden="true" />
              <h1 id="artifacts-heading">{t("artifacts.pageTitle")}</h1>
            </div>
          ) : activeConversation ? (
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
          ) : null}
        </header>
        {activeArtifact ? (
          <ArtifactDetailPage
            key={activeArtifact.id}
            artifactId={activeArtifact.id}
            language={language}
            projectName={
              activeArtifact.projectId
                ? projects.find((project) => project.id === activeArtifact.projectId)
                    ?.name ?? null
                : null
            }
          />
        ) : artifactsLibraryOpen ? (
          <ArtifactsPage
            language={language}
            projects={projects}
            onArtifactSelect={handleArtifactSelect}
          />
        ) : activeConversationId ? (
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
            onConversationStarted={handleConversationStarted}
            onConversationUpdated={handleConversationUpdated}
          />
        ) : null}
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
        hitlEnabled={hitlEnabled}
        hitlSaveError={hitlSaveError}
        onHitlChange={handleHitlChange}
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
      <ReviewCardsPreviewDialog
        open={reviewCardsPreviewOpen}
        onClose={closeReviewCardsPreview}
      />
    </div>
  );
}

export default App;
