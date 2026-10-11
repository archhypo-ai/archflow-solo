import type { ChatModelAdapter, ThreadMessage } from "@assistant-ui/react";
import type { AppLanguage } from "../../../i18n";
import { streamChatMessage } from "../api/chatClient";

type ChatModelAdapterOptions = {
  threadId: string;
  language: AppLanguage;
  projectId: string | null;
  onConversationUpdated: (
    threadId: string,
    title: string,
    preview: string,
    projectId: string | null,
  ) => void;
};

type UserMessage = Extract<ThreadMessage, { role: "user" }>;
type AssistantMessage = Extract<ThreadMessage, { role: "assistant" }>;
type AssistantContent = AssistantMessage["content"];
type AssistantPart = AssistantContent[number];
type ToolCallPart = Extract<AssistantPart, { type: "tool-call" }>;

function textFromMessage(message: UserMessage) {
  return message.content
    .filter((part) => part.type === "text")
    .map((part) => (part.type === "text" ? part.text : ""))
    .join("")
    .trim();
}

function parseToolArgs(text: string): ToolCallPart["args"] {
  if (!text.trim()) return {} as ToolCallPart["args"];
  try {
    const value: unknown = JSON.parse(text);
    return (value && typeof value === "object" ? value : {}) as ToolCallPart["args"];
  } catch {
    return {} as ToolCallPart["args"];
  }
}

export function createChatModelAdapter({
  threadId,
  language,
  projectId,
  onConversationUpdated,
}: ChatModelAdapterOptions): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      const latestUserMessage = [...messages]
        .reverse()
        .find((message): message is UserMessage => message.role === "user");
      const text = latestUserMessage ? textFromMessage(latestUserMessage) : "";
      if (!text) return;

      const content: AssistantPart[] = [];
      let phase = "thinking";
      let completed = false;

      const publish = () => ({
        content: [...content],
        metadata: { custom: { phase } },
      });

      for await (const event of streamChatMessage(
        threadId,
        text,
        language,
        projectId,
        abortSignal,
      )) {
        switch (event.type) {
          case "phase":
            phase = event.phase;
            break;
          case "tool_call_start":
            phase = "using_tools";
            content.push({
              type: "tool-call",
              toolCallId: event.tool_call_id,
              toolName: event.name,
              args: {} as ToolCallPart["args"],
              argsText: "",
            });
            break;
          case "tool_call_delta":
            for (let index = content.length - 1; index >= 0; index -= 1) {
              const part = content[index];
              if (part?.type !== "tool-call" || part.toolCallId !== event.tool_call_id) {
                continue;
              }
              const argsText = part.argsText + event.text;
              content[index] = {
                ...part,
                argsText,
                args: parseToolArgs(argsText),
              };
              break;
            }
            break;
          case "tool_result":
            for (let index = 0; index < content.length; index += 1) {
              const part = content[index];
              if (part?.type === "tool-call" && part.toolCallId === event.tool_call_id) {
                content[index] = {
                  ...part,
                  result: event.output,
                  isError: event.is_error,
                };
                break;
              }
            }
            break;
          case "text_delta": {
            phase = "answering";
            const textIndex = content.findIndex((part) => part.type === "text");
            if (textIndex >= 0 && content[textIndex]?.type === "text") {
              const part = content[textIndex];
              content[textIndex] = { ...part, text: part.text + event.text };
            } else {
              content.push({ type: "text", text: event.text });
            }
            break;
          }
          case "done":
            completed = true;
            onConversationUpdated(
              event.thread_id,
              event.title,
              event.message,
              projectId,
            );
            continue;
          case "error":
            throw new Error(event.message);
        }

        yield publish();
      }

      if (!completed && !abortSignal.aborted) {
        throw new Error("Chat stream ended before the response was complete");
      }
    },
  };
}
