import type { ChatModelAdapter, ThreadMessage } from "@assistant-ui/react";
import type { AppLanguage } from "../../../i18n";
import { sendChatMessage } from "../api/chatClient";

type ChatModelAdapterOptions = {
  threadId: string;
  language: AppLanguage;
  onConversationUpdated: (threadId: string, title: string) => void;
};

function textFromMessage(message: Extract<ThreadMessage, { role: "user" }>) {
  return message.content
    .filter((part) => part.type === "text")
    .map((part) => (part.type === "text" ? part.text : ""))
    .join("")
    .trim();
}

export function createChatModelAdapter({
  threadId,
  language,
  onConversationUpdated,
}: ChatModelAdapterOptions): ChatModelAdapter {
  return {
    async run({ messages }) {
      const latestUserMessage = [...messages]
        .reverse()
        .find(
          (message): message is Extract<ThreadMessage, { role: "user" }> =>
            message.role === "user",
        );
      const text = latestUserMessage ? textFromMessage(latestUserMessage) : "";
      if (!text) return { content: [] };

      const turn = await sendChatMessage(threadId, text, language);
      onConversationUpdated(turn.thread_id, turn.title);

      return {
        content: [{ type: "text", text: turn.message }],
      };
    },
  };
}
