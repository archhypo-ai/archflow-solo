import { useMemo, useState } from "react";
import {
  type AppendMessage,
  type ThreadMessage,
  useExternalStoreRuntime,
} from "@assistant-ui/react";

type UserThreadMessage = Extract<ThreadMessage, { role: "user" }>;

function newId() {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `local-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/**
 * Local-only assistant-ui runtime used while the desktop shell is being built.
 * It stores drafted messages in React state and does not call the agent.
 */
export function useLocalChatRuntime() {
  const [messages, setMessages] = useState<ThreadMessage[]>([]);

  const store = useMemo(
    () => ({
      messages,
      isRunning: false,
      isLoading: false,
      setMessages: (nextMessages: readonly ThreadMessage[]) => {
        setMessages([...nextMessages]);
      },
      onNew: async (message: AppendMessage) => {
        const userMessage: UserThreadMessage = {
          ...message,
          id: newId(),
          role: "user",
          content: message.content as UserThreadMessage["content"],
          createdAt: message.createdAt ?? new Date(),
          attachments: message.attachments ?? [],
          metadata: { custom: message.metadata?.custom ?? {} },
        };
        setMessages((current) => [...current, userMessage]);
      },
    }),
    [messages],
  );

  return useExternalStoreRuntime(store);
}
