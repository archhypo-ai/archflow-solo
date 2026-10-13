import {
  AuiIf,
  ErrorPrimitive,
  MessagePrimitive,
  useAuiState,
} from "@assistant-ui/react";
import { useTranslation } from "react-i18next";
import { ChatMarkdownText } from "./ChatMarkdownText";
import { ChatMessageActions } from "./ChatMessageActions";
import { ChatToolCall, ChatToolCallGroup } from "./ChatToolCalls";
import {
  HypothesisReviewCard,
  isPendingHypothesisReview,
} from "./HypothesisReviewCard";

export function ChatAssistantMessage() {
  const { t } = useTranslation();
  const phase = useAuiState(({ message }) => message.metadata.custom.phase);
  const hypothesisReview = useAuiState(
    ({ message }) => message.metadata.custom.hypothesisReview,
  );
  const hasRunningTool = useAuiState(({ message }) =>
    message.parts.some(
      (part) => part.type === "tool-call" && part.status.type === "running",
    ),
  );
  const workingLabel = hasRunningTool
    ? t("chat.usingTools")
    : phase === "answering"
      ? t("chat.answering")
      : t("chat.thinking");

  return (
    <MessagePrimitive.Root className="chat-message chat-message-assistant">
      <div className="chat-message-content">
        <MessagePrimitive.Parts
          components={{
            Text: ChatMarkdownText,
            ToolGroup: ChatToolCallGroup,
            tools: { Fallback: ChatToolCall },
          }}
        />
        {isPendingHypothesisReview(hypothesisReview) && (
          <HypothesisReviewCard review={hypothesisReview} />
        )}
        <AuiIf condition={(state) => state.message.status?.type === "running"}>
          <span className="chat-working-indicator" role="status">
            <span className="chat-working-indicator-dot" aria-hidden="true">
              ●
            </span>
            <span>{workingLabel}</span>
          </span>
        </AuiIf>
        <MessagePrimitive.Error>
          <div className="chat-message-error">
            <ErrorPrimitive.Message />
          </div>
        </MessagePrimitive.Error>
      </div>
      <ChatMessageActions />
    </MessagePrimitive.Root>
  );
}
