import type { ChatModelAdapter, ThreadMessage } from "@assistant-ui/react";

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
      const latestUserMessage = userMessages[userMessages.length - 1];
      const userText =
        latestUserMessage?.content
          .filter((part) => part.type === "text")
          .map((part) => part.text)
          .join("") ?? "";
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
            text: userText
              ? `Recebi sua mensagem: “${userText}”.\n\nEsta é uma resposta local de demonstração. A integração com o agente LangGraph será feita na próxima etapa.`
              : "Esta é uma resposta local de demonstração. O agente LangGraph será conectado na próxima etapa.",
          },
        ],
      };
    },
  };
}
