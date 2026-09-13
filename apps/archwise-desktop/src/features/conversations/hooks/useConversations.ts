import { useCallback, useEffect, useRef, useState } from "react";
import { listThreads } from "../../agent";
import type { Conversation } from "../types";

const INITIAL_LOAD_ATTEMPTS = 40;
const INITIAL_LOAD_INTERVAL_MS = 250;

function newId() {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `desktop-${Date.now()}`;
}

function wait(milliseconds: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, milliseconds));
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState(newId);
  const [isLoading, setIsLoading] = useState(true);
  const initialSelectionPending = useRef(true);

  const refreshConversations = useCallback(async () => {
    const threads = await listThreads();
    const nextConversations = threads.map((thread) => ({
      id: thread.thread_id,
      label: thread.title,
      // Pinning is not exposed by the current backend contract yet.
      pinned: false,
    }));

    setConversations(nextConversations);
    setActiveConversationId((current) =>
      current && nextConversations.some((item) => item.id === current)
        ? current
        : nextConversations[0]?.id ?? current,
    );
  }, []);

  useEffect(() => {
    let active = true;

    const loadThreads = async () => {
      for (let attempt = 0; attempt < INITIAL_LOAD_ATTEMPTS; attempt += 1) {
        try {
          const threads = await listThreads();
          if (!active) return;

          const loaded = threads.map((thread) => ({
            id: thread.thread_id,
            label: thread.title,
            pinned: false,
          }));
          setConversations(loaded);
          if (initialSelectionPending.current && loaded[0]) {
            setActiveConversationId(loaded[0].id);
          }
          initialSelectionPending.current = false;
          setIsLoading(false);
          return;
        } catch {
          if (attempt < INITIAL_LOAD_ATTEMPTS - 1) {
            await wait(INITIAL_LOAD_INTERVAL_MS);
          }
        }
      }

      if (active) {
        initialSelectionPending.current = false;
        setIsLoading(false);
      }
    };

    void loadThreads();
    return () => {
      active = false;
    };
  }, []);

  const newConversation = useCallback(() => {
    initialSelectionPending.current = false;
    setActiveConversationId(newId());
  }, []);

  const selectConversation = useCallback((conversation: Conversation) => {
    initialSelectionPending.current = false;
    setActiveConversationId(conversation.id);
  }, []);

  return {
    conversations,
    activeConversationId,
    isLoading,
    newConversation,
    refreshConversations,
    selectConversation,
  };
}
