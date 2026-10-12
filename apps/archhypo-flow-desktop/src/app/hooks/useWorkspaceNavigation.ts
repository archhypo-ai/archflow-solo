import { useCallback, useEffect, useState } from "react";
import type { ConversationSummary } from "../../features/conversations/types";
import type { Project } from "../../features/projects/types";

type UseWorkspaceNavigationOptions = {
  conversations: ConversationSummary[];
  conversationsLoaded: boolean;
  projects: Project[];
};

function newConversationId(): string {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `thread-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function useWorkspaceNavigation({
  conversations,
  conversationsLoaded,
  projects,
}: UseWorkspaceNavigationOptions) {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [pendingProjectId, setPendingProjectId] = useState<string | null>(null);

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

  useEffect(() => {
    if (!conversationsLoaded) return;
    setActiveConversationId(
      (current) => current ?? conversations[0]?.threadId ?? newConversationId(),
    );
  }, [conversations, conversationsLoaded]);

  const startNewConversation = useCallback(() => {
    setActiveProjectId(null);
    setPendingProjectId(null);
    setActiveConversationId(newConversationId());
  }, []);

  const openProjectHome = useCallback((projectId: string) => {
    setActiveConversationId(newConversationId());
    setPendingProjectId(projectId);
    setActiveProjectId(projectId);
  }, []);

  const selectConversation = useCallback(
    (threadId: string) => {
      const selected = conversations.find(
        (conversation) => conversation.threadId === threadId,
      );
      setActiveProjectId(null);
      setPendingProjectId(selected?.projectId ?? null);
      setActiveConversationId(threadId);
    },
    [conversations],
  );

  const handleConversationDeleted = useCallback((threadId: string) => {
    setActiveConversationId((current) =>
      current === threadId ? newConversationId() : current,
    );
  }, []);

  const handleProjectDeleted = useCallback(
    (projectId: string) => {
      if (
        activeProjectId === projectId ||
        activeConversation?.projectId === projectId ||
        pendingProjectId === projectId
      ) {
        setActiveConversationId(newConversationId());
      }
      if (activeProjectId === projectId) setActiveProjectId(null);
      if (pendingProjectId === projectId) setPendingProjectId(null);
    },
    [activeConversation?.projectId, activeProjectId, pendingProjectId],
  );

  return {
    activeConversationId,
    activeProjectId,
    pendingProjectId,
    activeConversation,
    activeProject,
    chatProject,
    projectLandingProject,
    isProjectLanding,
    isNewConversationActive,
    startNewConversation,
    openProjectHome,
    selectConversation,
    handleConversationDeleted,
    handleProjectDeleted,
  };
}
