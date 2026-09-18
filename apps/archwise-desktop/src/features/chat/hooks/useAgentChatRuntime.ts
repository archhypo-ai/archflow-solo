import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  type AppendMessage,
  type ThreadMessage,
  useExternalStoreRuntime,
} from "@assistant-ui/react";
import {
  attachFolderContext,
  attachFolderPath,
  cancelChatRun,
  deleteFolderContext,
  getThread,
  sendChatMessage,
} from "../../agent";
import type { BackendFolderContext, BackendThread } from "../../agent";
import { useI18n } from "../../../i18n";

type UserThreadMessage = Extract<ThreadMessage, { role: "user" }>;
type AssistantThreadMessage = Extract<ThreadMessage, { role: "assistant" }>;

type UseAgentChatRuntimeOptions = {
  persisted?: boolean;
  onConversationStarted?: (threadId: string, message: string) => void;
  onRegisterCancellation?: (
    threadId: string,
    cancel: () => Promise<void>,
  ) => () => void;
  onThreadUpdated?: () => void;
};

function newId(prefix: string) {
  const id =
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${id}`;
}

function userText(content: UserThreadMessage["content"]) {
  return content
    .filter((part) => part.type === "text")
    .map((part) => (part.type === "text" ? part.text : ""))
    .join("")
    .trim();
}

function userMessageFromAppend(message: AppendMessage): UserThreadMessage {
  return {
    ...message,
    id: newId("user"),
    role: "user",
    content: message.content as UserThreadMessage["content"],
    createdAt: message.createdAt ?? new Date(),
    attachments: message.attachments ?? [],
    metadata: { custom: message.metadata?.custom ?? {} },
  };
}

function assistantMessage(
  id: string,
  text: string,
  status: AssistantThreadMessage["status"] = {
    type: "complete",
    reason: "stop",
  },
): AssistantThreadMessage {
  return {
    id,
    role: "assistant",
    createdAt: new Date(),
    content: [{ type: "text", text }],
    status,
    metadata: {
      unstable_state: null,
      unstable_annotations: [],
      unstable_data: [],
      steps: [],
      custom: { agent: "archwise" },
    },
  };
}

function restoreMessages(thread: BackendThread): ThreadMessage[] {
  return thread.messages.map((message, index) => {
    const id = `${thread.thread_id}-${message.role}-${index}`;
    if (message.role === "user") {
      return {
        id,
        role: "user" as const,
        content: [{ type: "text", text: message.content }],
        createdAt: new Date(),
        attachments: [],
        metadata: { custom: { restored: true } },
      };
    }
    return assistantMessage(id, message.content);
  });
}

/** Bridge assistant-ui to the HTTP client used by the desktop webview. */
export function useAgentChatRuntime(
  threadId: string,
  {
    persisted = true,
    onConversationStarted,
    onRegisterCancellation,
    onThreadUpdated,
  }: UseAgentChatRuntimeOptions = {},
) {
  const { t } = useI18n();
  const [messages, setMessages] = useState<ThreadMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [folderContext, setFolderContext] =
    useState<BackendFolderContext | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const cancelPromiseRef = useRef<Promise<void> | null>(null);
  const generationRef = useRef(0);
  const runIdRef = useRef<string | null>(null);
  const pendingMessageIdRef = useRef<string | null>(null);

  const cancelActiveRun = useCallback(async () => {
    setIsRunning(false);
    if (cancelPromiseRef.current) {
      await cancelPromiseRef.current;
      return;
    }

    const runId = runIdRef.current;
    const pendingId = pendingMessageIdRef.current;
    if (pendingId) {
      setMessages((current) =>
        current.map((item) =>
          item.id === pendingId
            ? assistantMessage(pendingId, "", {
                type: "incomplete",
                reason: "cancelled",
              })
            : item,
        ),
      );
    }
    abortRef.current?.abort();
    if (!runId) return;

    const cancellation = cancelChatRun(runId)
      .catch(() => undefined)
      .then(() => undefined);
    cancelPromiseRef.current = cancellation;
    await cancellation;
  }, []);

  useEffect(() => {
    const generation = ++generationRef.current;
    abortRef.current?.abort();
    setIsLoading(true);
    setIsRunning(false);
    setMessages([]);
    setFolderContext(null);

    if (!persisted) {
      setIsLoading(false);
      return;
    }

    void getThread(threadId)
      .then((thread) => {
        if (generationRef.current !== generation) return;
        setMessages(thread ? restoreMessages(thread) : []);
        setFolderContext(thread?.folder_context ?? null);
      })
      .catch(() => {
        // A new thread has no checkpoint until its first message is sent.
      })
      .finally(() => {
        if (generationRef.current === generation) setIsLoading(false);
      });

    return () => {
      void cancelActiveRun();
    };
  }, [cancelActiveRun, threadId]);

  useEffect(() => {
    return onRegisterCancellation?.(threadId, cancelActiveRun);
  }, [cancelActiveRun, onRegisterCancellation, threadId]);

  const onFolderPathSelected = useCallback(
    async (folderPath: string) => {
      const context = await attachFolderPath(threadId, folderPath);
      setFolderContext(context);
      onConversationStarted?.(threadId, context.folder_name);
    },
    [onConversationStarted, threadId],
  );

  const onFolderSelected = useCallback(
    async (folderName: string, files: File[]) => {
      const context = await attachFolderContext(threadId, folderName, files);
      setFolderContext(context);
      onConversationStarted?.(threadId, folderName);
    },
    [onConversationStarted, threadId],
  );

  const onFolderRemoved = useCallback(async () => {
    await deleteFolderContext(threadId);
    setFolderContext(null);
  }, [threadId]);

  const onNew = useCallback(
    async (message: AppendMessage) => {
      if (isLoading || isRunning) return;

      const text = userText(message.content as UserThreadMessage["content"]);
      if (!text) return;

      const generation = generationRef.current;
      const controller = new AbortController();
      const runId = newId("run");
      cancelPromiseRef.current = null;
      runIdRef.current = runId;
      abortRef.current = controller;
      const userMessage = userMessageFromAppend(message);
      const pendingId = newId("assistant-pending");
      const pendingMessage: AssistantThreadMessage = {
        ...assistantMessage(pendingId, ""),
        content: [],
        status: { type: "running" },
      };
      pendingMessageIdRef.current = pendingId;

      onConversationStarted?.(threadId, text);
      setMessages((current) => [...current, userMessage, pendingMessage]);
      setIsRunning(true);

      try {
        const result = await sendChatMessage(
          threadId,
          text,
          controller.signal,
          runId,
        );
        if (
          generationRef.current !== generation ||
          controller.signal.aborted
        ) {
          return;
        }

        const persistedThread = await getThread(threadId).catch(() => null);
        if (
          generationRef.current !== generation ||
          controller.signal.aborted
        ) {
          return;
        }

        if (persistedThread) {
          // Reload the backend's user-visible projection so old internal
          // workflow prompts cannot remain in the local chat state.
          setMessages(restoreMessages(persistedThread));
        } else {
          setMessages((current) =>
            current.map((item) =>
              item.id === pendingId
                ? assistantMessage(pendingId, result.message)
                : item,
            ),
          );
        }
        onThreadUpdated?.();
      } catch (error) {
        if (
          controller.signal.aborted ||
          generationRef.current !== generation
        ) {
          return;
        }

        const detail =
          error instanceof Error ? error.message : t("chat.executionError");
        setMessages((current) =>
          current.map((item) =>
            item.id === pendingId
              ? assistantMessage(pendingId, detail, {
                  type: "incomplete",
                  reason: "error",
                  error: detail,
                })
              : item,
          ),
        );
      } finally {
        if (generationRef.current === generation) {
          if (abortRef.current === controller) abortRef.current = null;
          if (runIdRef.current === runId) runIdRef.current = null;
          if (pendingMessageIdRef.current === pendingId) {
            pendingMessageIdRef.current = null;
          }
          if (cancelPromiseRef.current) cancelPromiseRef.current = null;
          setIsRunning(false);
        }
      }
    },
    [
      isLoading,
      isRunning,
      onConversationStarted,
      onThreadUpdated,
      t,
      threadId,
    ],
  );

  const onCancel = useCallback(async () => {
    const pendingId = pendingMessageIdRef.current;
    await cancelActiveRun();

    // assistant-ui resynchronizes its repository after onCancel returns.
    // Apply the terminal status after that resync so the pending message does
    // not become running again.
    if (pendingId) {
      setTimeout(() => {
        setMessages((current) =>
          current.map((item) =>
            item.id === pendingId
              ? assistantMessage(pendingId, "", {
                  type: "incomplete",
                  reason: "cancelled",
                })
              : item,
          ),
        );
      }, 0);
    }
  }, [cancelActiveRun]);

  const store = useMemo(
    () => ({
      messages,
      isRunning,
      isLoading,
      setMessages: (nextMessages: readonly ThreadMessage[]) => {
        setMessages([...nextMessages]);
      },
      onNew,
      onCancel,
    }),
    [isLoading, isRunning, messages, onCancel, onNew],
  );

  const runtime = useExternalStoreRuntime(store);

  return {
    runtime,
    folderContext,
    onFolderSelected,
    onFolderPathSelected,
    onFolderRemoved,
  };
}
