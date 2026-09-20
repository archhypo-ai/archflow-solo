import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AgentEvent } from "agent-stream-ts";
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
  getActiveRun,
  getThread,
  streamChatMessage,
} from "../../agent";
import type {
  BackendActiveRun,
  BackendFolderContext,
  BackendThread,
} from "../../agent";
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

type AssistantContent = AssistantThreadMessage["content"];
type ToolCallPart = Extract<
  AssistantContent[number],
  { type: "tool-call" }
>;

function assistantMessage(
  id: string,
  text: string,
  status: AssistantThreadMessage["status"] = {
    type: "complete",
    reason: "stop",
  },
  content: AssistantContent = [{ type: "text", text }],
): AssistantThreadMessage {
  return {
    id,
    role: "assistant",
    createdAt: new Date(),
    content,
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

function pendingAssistantMessage(id: string): AssistantThreadMessage {
  return {
    ...assistantMessage(id, "", { type: "running" }),
    content: [],
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

function parseToolArgs(text: string): ToolCallPart["args"] {
  if (!text.trim()) return {} as ToolCallPart["args"];
  try {
    const value: unknown = JSON.parse(text);
    return (value && typeof value === "object" ? value : {}) as ToolCallPart["args"];
  } catch {
    // assistant-ui accepts partial args through argsText. Keep an empty object
    // until the JSON becomes complete so renderers can still show progress.
    return {} as ToolCallPart["args"];
  }
}

function applyAgentEvent(
  current: ThreadMessage[],
  pendingId: string,
  event: AgentEvent,
): ThreadMessage[] {
  return current.map((message) => {
    if (message.id !== pendingId || message.role !== "assistant") {
      return message;
    }

    let content: AssistantContent = [...message.content];
    let status = message.status;
    let metadata = message.metadata;

    switch (event.type) {
      case "text_delta": {
        const textIndex = content.findIndex((part) => part.type === "text");
        if (textIndex >= 0 && content[textIndex]?.type === "text") {
          const textPart = content[textIndex];
          content = [
            ...content.slice(0, textIndex),
            { ...textPart, text: textPart.text + event.text },
            ...content.slice(textIndex + 1),
          ];
        } else {
          content = [...content, { type: "text", text: event.text }];
        }
        break;
      }
      case "tool_call_start": {
        const toolCall: ToolCallPart = {
          type: "tool-call",
          toolCallId: event.tool_call_id,
          toolName: event.name,
          args: {} as ToolCallPart["args"],
          argsText: "",
        };
        content = [...content, toolCall];
        break;
      }
      case "tool_call_delta": {
        content = content.map((part) => {
          if (part.type !== "tool-call" || part.toolCallId !== event.tool_call_id) {
            return part;
          }
          const argsText = part.argsText + event.text;
          return { ...part, argsText, args: parseToolArgs(argsText) };
        });
        break;
      }
      case "tool_result":
        content = content.map((part) =>
          part.type === "tool-call" && part.toolCallId === event.tool_call_id
            ? { ...part, result: event.output }
            : part,
        );
        break;
      case "interrupt": {
        const toolCall: ToolCallPart = {
          type: "tool-call",
          toolCallId: event.interrupt_id,
          toolName: "human_input",
          args: {
            message: event.message,
            ...(event.payload ? { payload: event.payload } : {}),
          } as ToolCallPart["args"],
          argsText: JSON.stringify({
            message: event.message,
            ...(event.payload ? { payload: event.payload } : {}),
          }),
          interrupt: {
            type: "human",
            payload: event.payload ?? { message: event.message },
          },
        };
        content = [...content, toolCall];
        status = { type: "requires-action", reason: "interrupt" };
        break;
      }
      case "done":
        status = { type: "complete", reason: "stop" };
        break;
      case "cancelled":
        status = { type: "incomplete", reason: "cancelled" };
        break;
      case "error":
        status = { type: "incomplete", reason: "error", error: event.message };
        break;
      case "phase":
        metadata = {
          ...message.metadata,
          custom: { ...message.metadata.custom, phase: event.phase },
        };
        break;
    }

    return { ...message, content, status, metadata };
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
  const [activeRun, setActiveRun] = useState<BackendActiveRun | null>(null);
  const [folderContext, setFolderContext] =
    useState<BackendFolderContext | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const cancelPromiseRef = useRef<Promise<void> | null>(null);
  const generationRef = useRef(0);
  const runIdRef = useRef<string | null>(null);
  const pendingMessageIdRef = useRef<string | null>(null);

  const cancelActiveRun = useCallback(async () => {
    setIsRunning(false);
    setActiveRun(null);
    if (cancelPromiseRef.current) {
      await cancelPromiseRef.current;
      return;
    }

    const runId = runIdRef.current;
    const pendingId = pendingMessageIdRef.current;
    if (pendingId) {
      setMessages((current) =>
        current.map((item) =>
          item.id === pendingId && item.role === "assistant"
            ? {
                ...item,
                status: { type: "incomplete", reason: "cancelled" },
              }
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
    // Keep an in-flight request alive while the conversation is out of view.
    runIdRef.current = null;
    pendingMessageIdRef.current = null;
    setIsLoading(true);
    setIsRunning(false);
    setActiveRun(null);
    setMessages([]);
    setFolderContext(null);

    const threadRequest = persisted
      ? getThread(threadId)
      : Promise.resolve<BackendThread | null>(null);
    const runRequest = getActiveRun(threadId).catch(() => null);

    void Promise.all([threadRequest, runRequest])
      .then(([thread, run]) => {
        if (generationRef.current !== generation) return;
        const restoredMessages = thread ? restoreMessages(thread) : [];
        setFolderContext(thread?.folder_context ?? null);
        if (run) {
          const pendingId = newId("assistant-pending");
          runIdRef.current = run.run_id;
          pendingMessageIdRef.current = pendingId;
          setMessages([
            ...restoredMessages,
            pendingAssistantMessage(pendingId),
          ]);
          setActiveRun(run);
          setIsRunning(true);
        } else {
          setMessages(restoredMessages);
        }
      })
      .catch(() => {
        // A new thread has no checkpoint until its first message is sent.
      })
      .finally(() => {
        if (generationRef.current === generation) setIsLoading(false);
      });

    return () => {
      // Leaving the view must not cancel the backend run or its request.
      // The next conversation mount will query its status and poll for its
      // persisted result.
    };
  // `persisted` only controls the initial hydration. A new thread becomes
  // persisted while its first run is active; rehydrating here would clear the
  // optimistic user message before the backend checkpoint is available.
  }, [threadId]);

  useEffect(() => {
    if (!activeRun) return;
    let stopped = false;

    const refreshActiveRun = async () => {
      const run = await getActiveRun(threadId).catch(() => undefined);
      if (stopped || run === undefined) return;
      if (run) return;

      const thread = await getThread(threadId).catch(() => null);
      if (stopped) return;
      if (thread) setMessages(restoreMessages(thread));
      setActiveRun(null);
      setIsRunning(false);
      runIdRef.current = null;
      pendingMessageIdRef.current = null;
      onThreadUpdated?.();
    };

    const interval = window.setInterval(() => {
      void refreshActiveRun();
    }, 1000);
    return () => {
      stopped = true;
      window.clearInterval(interval);
    };
  }, [activeRun, onThreadUpdated, threadId]);

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
      const pendingMessage = pendingAssistantMessage(pendingId);
      pendingMessageIdRef.current = pendingId;
      setActiveRun(null);

      onConversationStarted?.(threadId, text);
      setMessages((current) => [...current, userMessage, pendingMessage]);
      setIsRunning(true);

      try {
        await streamChatMessage(
          threadId,
          text,
          controller.signal,
          runId,
          (event) => {
            if (
              generationRef.current !== generation ||
              controller.signal.aborted
            ) {
              return;
            }
            setMessages((current) =>
              applyAgentEvent(current, pendingId, event),
            );
          },
        );
        if (
          generationRef.current !== generation ||
          controller.signal.aborted
        ) {
          return;
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
          current.map((item) => {
            if (item.id !== pendingId || item.role !== "assistant") {
              return item;
            }
            return {
              ...item,
              content:
                item.content.length > 0
                  ? [...item.content, { type: "text", text: detail }]
                  : [{ type: "text", text: detail }],
              status: { type: "incomplete", reason: "error", error: detail },
            };
          }),
        );
      } finally {
        if (generationRef.current === generation) {
          if (abortRef.current === controller) abortRef.current = null;
          if (runIdRef.current === runId) runIdRef.current = null;
          if (pendingMessageIdRef.current === pendingId) {
            pendingMessageIdRef.current = null;
          }
          if (cancelPromiseRef.current) cancelPromiseRef.current = null;
          setActiveRun(null);
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
            item.id === pendingId && item.role === "assistant"
              ? {
                  ...item,
                  status: { type: "incomplete", reason: "cancelled" },
                }
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
