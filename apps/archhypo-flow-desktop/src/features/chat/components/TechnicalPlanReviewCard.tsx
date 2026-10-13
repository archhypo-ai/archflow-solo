import { useAui } from "@assistant-ui/react";
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type {
  AssessmentLevel,
  HumanReviewDecision,
  PendingTechnicalPlanReview,
} from "../types";
import { ApprovedReviewSummary } from "./ApprovedReviewSummary";
import "./HumanReviewCard.css";
import "./TechnicalPlanReviewCard.css";

type TechnicalPlanReviewCardProps = {
  review: PendingTechnicalPlanReview;
};

const assessmentLevelKeys: Record<AssessmentLevel, string> = {
  "Very Low": "veryLow",
  Low: "low",
  Medium: "medium",
  High: "high",
  "Very High": "veryHigh",
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
        custom: { technicalPlanReview: decision, isReviewAction: true },
      },
      startRun: true,
    });
    setSubmittedDecision(decision);
  };

  if (submittedDecision?.decision === "approved") {
    return <ApprovedReviewSummary review={review} />;
  }

  const renderLevel = (level: AssessmentLevel) =>
    t(`chat.assessmentLevels.${assessmentLevelKeys[level]}`);

  return (
    <section
      className="human-review-card technical-plan-review-card"
      aria-label={t("chat.technicalPlanReviewTitle")}
    >
      <section
        className="technical-plan-review-section"
        aria-label={t("chat.technicalPlanAssessmentTitle")}
      >
        <h3 className="technical-plan-review-section-title">
          {t("chat.technicalPlanAssessmentTitle")}
        </h3>
        <div className="technical-plan-review-assessments">
          <AssessmentReviewItem
            label={t("chat.impactLabel")}
            level={renderLevel(review.assessment.impact)}
            levelTone={assessmentLevelKeys[review.assessment.impact]}
            justification={review.assessment.impact_justification}
          />
          <AssessmentReviewItem
            label={t("chat.uncertaintyLabel")}
            level={renderLevel(review.assessment.uncertainty)}
            levelTone={assessmentLevelKeys[review.assessment.uncertainty]}
            justification={review.assessment.uncertainty_justification}
          />
        </div>
      </section>

      <section
        className="technical-plan-review-section"
        aria-label={t("chat.technicalPlanTitle")}
      >
        <h3 className="technical-plan-review-section-title">
          {t("chat.technicalPlanTitle")}
        </h3>
        <p className="technical-plan-review-rationale">
          {review.technical_plan.rationale}
        </p>
        <ol className="technical-plan-review-items">
          {review.technical_plan.items.map((item, index) => (
            <li className="technical-plan-review-item" key={`${index}-${item.title}`}>
              <div className="technical-plan-review-item-heading">
                <span className="technical-plan-review-item-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h4>{item.title}</h4>
              </div>
              <PlanItemField
                label={t("chat.planObjectiveLabel")}
                value={item.objective}
              />
              <PlanItemField
                label={t("chat.planDescriptionLabel")}
                value={item.description}
              />
              <PlanItemField
                label={t("chat.planPatternLabel")}
                value={item.pattern}
                pattern
              />
              <PlanItemField
                label={t("chat.planTradeoffLabel")}
                value={item.tradeoff}
              />
            </li>
          ))}
        </ol>
      </section>

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

function AssessmentReviewItem({
  label,
  level,
  levelTone,
  justification,
}: {
  label: string;
  level: string;
  levelTone: string;
  justification: string;
}) {
  return (
    <section className="technical-plan-review-assessment">
      <div className="technical-plan-review-assessment-heading">
        <span className="technical-plan-review-assessment-label">{label}</span>
        <span
          className="technical-plan-review-level"
          data-level={levelTone}
        >
          {level}
        </span>
      </div>
      <p>{justification}</p>
    </section>
  );
}

function PlanItemField({
  label,
  value,
  pattern = false,
}: {
  label: string;
  value: string;
  pattern?: boolean;
}) {
  return (
    <div className="technical-plan-review-item-field">
      <span className="technical-plan-review-item-label">{label}</span>
      {pattern ? (
        <span className="technical-plan-review-pattern">{value}</span>
      ) : (
        <p>{value}</p>
      )}
    </div>
  );
}
