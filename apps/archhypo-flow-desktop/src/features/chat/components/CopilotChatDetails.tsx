import type { HumanReviewDecision, PendingHumanReview } from "../types";
import { createContext, useContext } from "react";
import { useTranslation } from "react-i18next";
import { A2uiMessageSurface } from "./A2uiMessageSurface";
import { ApprovedReviewSummary } from "./ApprovedReviewSummary";
import { HypothesisReviewCard, isPendingHypothesisReview } from "./HypothesisReviewCard";
import { TechnicalPlanReviewCard, isPendingTechnicalPlanReview } from "./TechnicalPlanReviewCard";

export const ARCHHYPO_ACTIVITY = "archhypo-chat-details";

export const ReviewActions = createContext<{
  running: boolean;
  submit: (review: PendingHumanReview, decision: HumanReviewDecision) => void;
}>({ running: false, submit: () => {} });

export type ChatDetails = {
  a2uiSurface?: unknown;
  hypothesisReview?: unknown;
  technicalPlanReview?: unknown;
  completedReview?: unknown;
  tools?: string[];
  error?: string;
};

export const copilotActivityRenderers = [{
  activityType: ARCHHYPO_ACTIVITY,
  content: {
    "~standard": {
      version: 1 as const,
      vendor: "archhypo",
      validate(value: unknown) {
        return value && typeof value === "object"
          ? { value: value as ChatDetails }
          : { issues: [{ message: "Expected chat details." }] };
      },
    },
  },
  render: ({ content, message }: { content: ChatDetails; message: { id: string } }) => {
    const { t } = useTranslation();
    const actions = useContext(ReviewActions);
    const { hypothesisReview, technicalPlanReview } = content;
    const completed = content.completedReview;
    const review = completed && typeof completed === "object" && "review" in completed
      ? completed.review
      : null;
    return (
      <div className="archhypo-copilot-details"
        {...(isPendingHypothesisReview(hypothesisReview) || isPendingTechnicalPlanReview(technicalPlanReview)
          ? { id: "chat-pending-review", tabIndex: -1 } : {})}>
        {content.tools?.length ? <small>{t("chat.usingTools")}: {content.tools.join(", ")}</small> : null}
        {Boolean(content.a2uiSurface) && <A2uiMessageSurface id={message.id} messages={content.a2uiSurface} />}
        {isPendingHypothesisReview(hypothesisReview) && <HypothesisReviewCard review={hypothesisReview} disabled={actions.running} onDecision={(decision) => actions.submit(hypothesisReview, decision)} />}
        {isPendingTechnicalPlanReview(technicalPlanReview) && <TechnicalPlanReviewCard review={technicalPlanReview} disabled={actions.running} onDecision={(decision) => actions.submit(technicalPlanReview, decision)} />}
        {(isPendingHypothesisReview(review) || isPendingTechnicalPlanReview(review)) && <ApprovedReviewSummary review={review} />}
        {content.error && <p role="alert">{content.error}</p>}
      </div>
    );
  },
}];
