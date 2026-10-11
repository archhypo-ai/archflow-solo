import type { ChatModelAdapter, ThreadMessage } from "@assistant-ui/react";
import i18n from "../../../i18n";

type DemoChatModelOptions = {
  onConversationStarted: (title: string) => void;
};

export function createDemoChatModel({
  onConversationStarted,
}: DemoChatModelOptions): ChatModelAdapter {
  return {
    async run({ messages }) {
      const userMessages = messages.filter(
        (message): message is Extract<ThreadMessage, { role: "user" }> =>
          message.role === "user",
      );
      const firstUserMessage = userMessages[0];
      const title =
        firstUserMessage?.content
          .filter((part) => part.type === "text")
          .map((part) => part.text)
          .join("")
          .trim()
          .slice(0, 44) ?? "";

      if (title) onConversationStarted(title);

      return {
        content: [
          {
            type: "text",
            text: i18n.t("chat.demoReply"),
          },
        ],
      };
    },
  };
}
