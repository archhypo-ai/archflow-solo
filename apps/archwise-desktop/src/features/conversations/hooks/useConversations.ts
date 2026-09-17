import { useCallback, useEffect, useRef, useState } from "react";
import {
  deleteThread,
  listThreads,
  updateThread,
} from "../../agent";
import type { BackendThreadSummary } from "../../agent";
import type { Conversation } from "../types";

const INITIAL_LOAD_ATTEMPTS = 40;
const INITIAL_LOAD_INTERVAL_MS = 250;
type CancellationHandler = () => Promise<void>;

function newId() {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `desktop-${Date.now()}`;
}

function wait(milliseconds: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, milliseconds));
}

function toConversation(thread: BackendThreadSummary): Conversation {
  return {
    id: thread.thread_id,
    label: thread.title,
    pinned: thread.pinned,
  };
}

function titleFromMessage(message: string) {
  return message.replace(/\s+/g, " ").trim().slice(0, 80).trim();
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState(newId);
  const [isLoading, setIsLoading] = useState(true);
  const initialSelectionPending = useRef(true);
  const cancellationHandlers = useRef(
    new Map<string, CancellationHandler>(),
  );
  const refreshGeneration = useRef(0);

  const refreshConversations = useCallback(async () => {
    const generation = ++refreshGeneration.current;
    const threads = await listThreads();
    if (generation !== refreshGeneration.current) return;
    const nextConversations = threads.map(toConversation);

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

          const loaded = threads.map(toConversation);
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
    setActiveConversationId((current) =>
      current && conversations.some((item) => item.id === current)
        ? newId()
        : current,
    );
  }, [conversations]);

  const ensureConversation = useCallback(
    (threadId: string, message: string) => {
      const title = titleFromMessage(message);
      setConversations((current) => {
        if (current.some((item) => item.id === threadId)) return current;
        return [{ id: threadId, label: title, pinned: false }, ...current];
      });
    },
    [],
  );

  const registerConversationCancellation = useCallback(
    (threadId: string, cancel: CancellationHandler) => {
      cancellationHandlers.current.set(threadId, cancel);
      return () => {
        if (cancellationHandlers.current.get(threadId) === cancel) {
          cancellationHandlers.current.delete(threadId);
        }
      };
    },
    [],
  );

  const selectConversation = useCallback((conversation: Conversation) => {
    initialSelectionPending.current = false;
    setActiveConversationId(conversation.id);
  }, []);

  const togglePinned = useCallback((conversation: Conversation) => {
    void updateThread(conversation.id, { pinned: !conversation.pinned })
      .then((updated) => {
        setConversations((current) =>
          current.map((item) =>
            item.id === updated.thread_id ? toConversation(updated) : item,
          ),
        );
      })
      .catch(() => undefined);
  }, []);

  const deleteConversation = useCallback((conversation: Conversation) => {
    const cancel = cancellationHandlers.current.get(conversation.id);
    refreshGeneration.current += 1;

    void (async () => {
      try {
        await cancel?.();
      } catch {
        // Deletion remains the source of truth if cancellation fails.
      }

      try {
        await deleteThread(conversation.id);
        refreshGeneration.current += 1;
        setConversations((current) =>
          current.filter((item) => item.id !== conversation.id),
        );
        setActiveConversationId((current) =>
          current === conversation.id ? newId() : current,
        );
      } catch {
        // Keep the conversation visible when the backend deletion fails.
      }
    })();
  }, []);

  return {
    conversations,
    activeConversationId,
    ensureConversation,
    isLoading,
    newConversation,
    registerConversationCancellation,
    refreshConversations,
    selectConversation,
    togglePinned,
    deleteConversation,
  };
}
