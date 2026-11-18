import type { AbstractAgent } from "@ag-ui/client";
import type { ChatModelAdapter, ThreadMessage } from "@assistant-ui/react";
import { EventType } from "@ag-ui/core";
import type { AppLanguage } from "../../../i18n";
import { streamChatMessage } from "../api/chatClient";
import { attachmentFolder } from "./documentAttachmentAdapter";
import type {
  HumanReviewDecision,
  PendingHumanReview,
} from "../types";

type ChatModelAdapterOptions = {
  agent?: AbstractAgent;
  threadId: string;
  language: AppLanguage;
  projectId: string | null;
  onConversationStarted: (
    threadId: string,
    title: string,
    userMessage: string,
    projectId: string | null,
  ) => void;
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
  agent,
  threadId,
  language,
  projectId,
  onConversationStarted,
  onConversationUpdated,
}: ChatModelAdapterOptions): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      const latestUserMessage = [...messages]
        .reverse()
        .find((message): message is UserMessage => message.role === "user");
      const text = latestUserMessage ? textFromMessage(latestUserMessage) : "";
      const attachments = (latestUserMessage?.attachments ?? []).flatMap((attachment) =>
        attachment.content.flatMap((part) => {
          if (part.type !== "file" || !part.data.startsWith("data:")) return [];
          const encoded = part.data.split(",", 2)[1];
          const folder = attachmentFolder(attachment.file);
          return encoded ? [{
            name: attachment.name,
            data: encoded,
            ...(folder ? { folder_id: folder.id, folder_name: folder.name } : {}),
          }] : [];
        }),
      );
      const hypothesisReview = latestUserMessage
        ? reviewDecisionFromMessage(latestUserMessage, "hypothesisReview")
        : undefined;
      const technicalPlanReview = latestUserMessage
        ? reviewDecisionFromMessage(latestUserMessage, "technicalPlanReview")
        : undefined;
      const isReviewAction = Boolean(hypothesisReview || technicalPlanReview);
      if (!text && !isReviewAction && !attachments.length) return;

      const content: AssistantPart[] = [];
      let phase = "thinking";
      let completed = false;
      let pendingReview: PendingHumanReview | undefined;
      let a2uiSurface: unknown[] = [];

      const publish = () => ({
        content: [...content],
        metadata: {
          custom: {
            phase,
            ...(a2uiSurface.length ? { a2uiSurface } : {}),
            ...(pendingReview?.kind === "hypothesis_review"
              ? { hypothesisReview: pendingReview }
              : {}),
            ...(pendingReview?.kind === "technical_plan_review"
              ? { technicalPlanReview: pendingReview }
              : {}),
          },
        },
      });

      const source = streamChatMessage(
        threadId,
        isReviewAction ? "" : text,
        language,
        projectId,
        abortSignal,
        hypothesisReview,
        technicalPlanReview,
        attachments,
        latestUserMessage?.metadata.custom.interruptId,
        agent,
      );
      for await (const event of source) {
        switch (event.type) {
          case EventType.RUN_STARTED:
          case EventType.TEXT_MESSAGE_START:
          case EventType.TEXT_MESSAGE_END:
          case EventType.TOOL_CALL_END:
            continue;
          case EventType.CUSTOM:
            if (event.name === "archhypo.a2ui") {
              const batch = Array.isArray(event.value) ? event.value : [event.value];
              if (a2uiSurface.length + batch.length <= 200) {
                a2uiSurface = [...a2uiSurface, ...batch];
              }
              break;
            }
            if (event.name === "archhypo.phase") {
              phase = event.value.phase;
              break;
            }
            if (event.value.user_message.trim()) {
              onConversationStarted(
                event.value.thread_id,
                event.value.title,
                event.value.user_message,
                event.value.project_id,
              );
            }
            continue;
          case EventType.TOOL_CALL_START:
            phase = "using_tools";
            content.push({
              type: "tool-call",
              toolCallId: event.toolCallId,
              toolName: event.toolCallName,
              args: {} as ToolCallPart["args"],
              argsText: "",
            });
            break;
          case EventType.TOOL_CALL_ARGS:
            for (let index = content.length - 1; index >= 0; index -= 1) {
              const part = content[index];
              if (part?.type !== "tool-call" || part.toolCallId !== event.toolCallId) {
                continue;
              }
              const argsText = part.argsText + event.delta;
              content[index] = {
                ...part,
                argsText,
                args: parseToolArgs(argsText),
              };
              break;
            }
            break;
          case EventType.TOOL_CALL_RESULT:
            for (let index = 0; index < content.length; index += 1) {
              const part = content[index];
              if (part?.type === "tool-call" && part.toolCallId === event.toolCallId) {
                content[index] = {
                  ...part,
                  result: JSON.parse(event.content),
                  isError: event.metadata.isError,
                };
                break;
              }
            }
            break;
          case EventType.TEXT_MESSAGE_CONTENT: {
            phase = "answering";
            const textIndex = content.findIndex((part) => part.type === "text");
            if (textIndex >= 0 && content[textIndex]?.type === "text") {
              const part = content[textIndex];
              content[textIndex] = { ...part, text: part.text + event.delta };
            } else {
              content.push({ type: "text", text: event.delta });
            }
            break;
          }
          case EventType.RUN_FINISHED: {
            completed = true;
            if (event.outcome?.type === "interrupt") {
              const review = event.outcome.interrupts[0]?.metadata?.archhypoReview as
                PendingHumanReview | null | undefined;
              pendingReview = review
                ? { ...review, interrupt_id: event.outcome.interrupts[0].id }
                : undefined;
              phase = pendingReview?.kind === "technical_plan_review"
                ? "reviewing_technical_plan"
                : "reviewing_hypothesis";
              break;
            }
            if (event.result) {
              const index = content.findIndex((part) => part.type === "text");
              if (index >= 0 && content[index]?.type === "text" &&
                content[index].text !== event.result.message) {
                content[index] = { type: "text", text: event.result.message };
                yield publish();
              }
              onConversationUpdated(
                event.threadId, event.result.title, event.result.message, projectId,
              );
            }
            continue;
          }
          case EventType.RUN_ERROR:
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

function reviewDecisionFromMessage(
  message: UserMessage,
  metadataKey: "hypothesisReview" | "technicalPlanReview",
): HumanReviewDecision | undefined {
  const value = message.metadata.custom[metadataKey];
  if (!value || typeof value !== "object" || !("decision" in value)) {
    return undefined;
  }
  const decision = value.decision;
  if (decision === "approved") {
    return "reason" in value && typeof value.reason === "string" && value.reason.trim()
      ? { decision, reason: value.reason.trim() }
      : { decision };
  }
  if (
    decision === "rejected" &&
    "reason" in value &&
    typeof value.reason === "string" &&
    value.reason.trim()
  ) {
    return { decision, reason: value.reason.trim() };
  }
  return undefined;
}
