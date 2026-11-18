import {
  AuiIf,
  ErrorPrimitive,
  MessagePrimitive,
  useAuiState,
} from "@assistant-ui/react";
import { useTranslation } from "react-i18next";
import { ChatMarkdownText } from "./ChatMarkdownText";
import { A2uiMessageSurface } from "./A2uiMessageSurface";
import { ChatMessageActions } from "./ChatMessageActions";
import { ChatToolCall, ChatToolCallGroup } from "./ChatToolCalls";
import { ApprovedReviewSummary } from "./ApprovedReviewSummary";
import {
  HypothesisReviewCard,
  isPendingHypothesisReview,
} from "./HypothesisReviewCard";
import {
  isPendingTechnicalPlanReview,
  TechnicalPlanReviewCard,
} from "./TechnicalPlanReviewCard";
import type { CompletedHumanReview } from "../types";

export function ChatAssistantMessage() {
  const { t } = useTranslation();
  const phase = useAuiState(({ message }) => message.metadata.custom.phase);
  const a2uiSurface = useAuiState(({ message }) => message.metadata.custom.a2uiSurface);
  const messageId = useAuiState(({ message }) => message.id);
  const hypothesisReview = useAuiState(
    ({ message }) => message.metadata.custom.hypothesisReview,
  );
  const technicalPlanReview = useAuiState(
    ({ message }) => message.metadata.custom.technicalPlanReview,
  );
  const completedHumanReview = useAuiState(
    ({ message }) => message.metadata.custom.completedHumanReview,
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
        {Boolean(a2uiSurface) && <A2uiMessageSurface id={messageId} messages={a2uiSurface} />}
        {isPendingHypothesisReview(hypothesisReview) && (
          <HypothesisReviewCard review={hypothesisReview} />
        )}
        {isPendingTechnicalPlanReview(technicalPlanReview) && (
          <TechnicalPlanReviewCard review={technicalPlanReview} />
        )}
        {isCompletedHumanReview(completedHumanReview) && (
          <ApprovedReviewSummary review={completedHumanReview.review} />
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

function isCompletedHumanReview(value: unknown): value is CompletedHumanReview {
  if (!value || typeof value !== "object" || !("kind" in value)) return false;
  if (
    !("review" in value) ||
    !("decision" in value) ||
    !("after_message_count" in value) ||
    typeof value.after_message_count !== "number" ||
    !value.decision ||
    typeof value.decision !== "object" ||
    !("decision" in value.decision) ||
    value.decision.decision !== "approved"
  ) {
    return false;
  }
  if (value.kind === "hypothesis_review") {
    return isPendingHypothesisReview(value.review);
  }
  if (value.kind === "technical_plan_review") {
    return isPendingTechnicalPlanReview(value.review);
  }
  return false;
}
