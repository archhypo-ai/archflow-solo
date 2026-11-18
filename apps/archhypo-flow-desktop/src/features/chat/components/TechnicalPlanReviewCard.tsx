import { useAui } from "@assistant-ui/react";
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type {
  AssessmentLevel,
  HumanReviewDecision,
  PendingTechnicalPlanReview,
} from "../types";
import { ApprovedReviewSummary } from "./ApprovedReviewSummary";
import { TechnicalPlanReviewContent } from "./TechnicalPlanReviewContent";
import "./HumanReviewCard.css";
import "./TechnicalPlanReviewCard.css";

type TechnicalPlanReviewCardProps = {
  review: PendingTechnicalPlanReview;
};

function isAssessmentLevel(value: unknown): value is AssessmentLevel {
  return (
    value === "Very Low" ||
    value === "Low" ||
    value === "Medium" ||
    value === "High" ||
    value === "Very High"
  );
}

export function isPendingTechnicalPlanReview(
  value: unknown,
): value is PendingTechnicalPlanReview {
  if (!value || typeof value !== "object" || !("kind" in value)) return false;
  if (value.kind !== "technical_plan_review" || !("assessment" in value)) {
    return false;
  }
  if (!("technical_plan" in value)) return false;

  const assessment = value.assessment;
  const plan = value.technical_plan;
  return (
    !!assessment &&
    typeof assessment === "object" &&
    "impact" in assessment &&
    isAssessmentLevel(assessment.impact) &&
    "impact_justification" in assessment &&
    typeof assessment.impact_justification === "string" &&
    "uncertainty" in assessment &&
    isAssessmentLevel(assessment.uncertainty) &&
    "uncertainty_justification" in assessment &&
    typeof assessment.uncertainty_justification === "string" &&
    !!plan &&
    typeof plan === "object" &&
    "rationale" in plan &&
    typeof plan.rationale === "string" &&
    "items" in plan &&
    Array.isArray(plan.items) &&
    plan.items.every(isTechnicalPlanItem)
  );
}

function isTechnicalPlanItem(value: unknown): boolean {
  if (!value || typeof value !== "object") return false;
  return (
    "title" in value &&
    typeof value.title === "string" &&
    "objective" in value &&
    typeof value.objective === "string" &&
    "description" in value &&
    typeof value.description === "string" &&
    "pattern" in value &&
    typeof value.pattern === "string" &&
    "tradeoff" in value &&
    typeof value.tradeoff === "string"
  );
}

export function TechnicalPlanReviewCard({
  review,
}: TechnicalPlanReviewCardProps) {
  const aui = useAui();
  const { t } = useTranslation();
  const reasonId = useId();
  const [note, setNote] = useState("");
  const [submittedDecision, setSubmittedDecision] =
    useState<HumanReviewDecision | null>(null);

  const submit = (decision: HumanReviewDecision) => {
    aui.thread.append({
      role: "user",
      content: [{ type: "text", text: "\u2063" }],
      metadata: {
        custom: { technicalPlanReview: decision, interruptId: review.interrupt_id, isReviewAction: true },
      },
      startRun: true,
    });
    setSubmittedDecision(decision);
  };

  if (submittedDecision?.decision === "approved") {
    return <ApprovedReviewSummary review={review} />;
  }

  return (
    <section
      className="human-review-card technical-plan-review-card"
      aria-label={t("chat.technicalPlanReviewTitle")}
    >
      <TechnicalPlanReviewContent review={review} />

      {submittedDecision ? (
        <p className="human-review-submitted" role="status">
          {t("chat.reviewSubmitted")}
        </p>
      ) : (
        <>
          <div className="human-review-note-section">
            <div className="human-review-note-heading">
              <label className="human-review-note-label" htmlFor={reasonId}>
                {t("chat.reviewNoteLabel")}
              </label>
              <span className="human-review-note-hint">
                {t("chat.reviewNoteHint")}
              </span>
            </div>
            <textarea
              id={reasonId}
              className="human-review-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder={t("chat.reviewReasonPlaceholder")}
              rows={2}
            />
          </div>
          <div className="human-review-footer">
            <div className="human-review-actions">
              <button
                className="human-review-reject"
                type="button"
                disabled={!note.trim()}
                onClick={() =>
                  submit({ decision: "rejected", reason: note.trim() })
                }
              >
                {t("chat.reviewReject")}
              </button>
              <button
                className="human-review-approve"
                type="button"
                onClick={() =>
                  submit({
                    decision: "approved",
                    ...(note.trim() ? { reason: note.trim() } : {}),
                  })
                }
              >
                {t("chat.reviewApprove")}
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
