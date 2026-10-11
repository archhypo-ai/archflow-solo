import { useCallback, useEffect, useState } from "react";
import {
  deleteConversation as deleteConversationRequest,
  listConversations,
  updateConversation as updateConversationRequest,
} from "../api/conversationClient";
import type { ConversationSummary } from "../types";

function sortConversations(items: ConversationSummary[]): ConversationSummary[] {
  return [...items].sort((left, right) => {
    if (left.pinned !== right.pinned) return left.pinned ? -1 : 1;
    return right.updatedAt.localeCompare(left.updatedAt);
  });
}

export function useConversations() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    void listConversations()
      .then((items) => {
        if (!active) return;
        setConversations(sortConversations(items));
        setLoaded(true);
      })
      .catch((error: unknown) => {
        console.error("Could not load conversations from the local API", error);
        if (active) setLoaded(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const updateFromChat = useCallback(
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
    },
    [],
  );

  const toggleConversationPin = useCallback(
    async (conversation: ConversationSummary) => {
      try {
        const updated = await updateConversationRequest(conversation.threadId, {
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

  const renameConversation = useCallback(
    async (threadId: string, title: string) => {
      const updated = await updateConversationRequest(threadId, { title });
      setConversations((current) =>
        sortConversations([
          updated,
          ...current.filter((item) => item.threadId !== updated.threadId),
        ]),
      );
    },
    [],
  );

  const deleteConversation = useCallback(async (threadId: string) => {
    await deleteConversationRequest(threadId);
    setConversations((current) =>
      current.filter((conversation) => conversation.threadId !== threadId),
    );
  }, []);

  const removeProjectConversations = useCallback((projectId: string) => {
    setConversations((current) =>
      current.filter((conversation) => conversation.projectId !== projectId),
    );
  }, []);

  return {
    conversations,
    conversationsLoaded: loaded,
    updateFromChat,
    toggleConversationPin,
    renameConversation,
    deleteConversation,
    removeProjectConversations,
  };
}
