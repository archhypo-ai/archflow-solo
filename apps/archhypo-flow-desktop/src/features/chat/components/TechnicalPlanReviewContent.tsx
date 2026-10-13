import { useTranslation } from "react-i18next";
import type { AssessmentLevel, PendingTechnicalPlanReview } from "../types";
import "./TechnicalPlanReviewCard.css";

const assessmentLevelKeys: Record<AssessmentLevel, string> = {
  "Very Low": "veryLow",
  Low: "low",
  Medium: "medium",
  High: "high",
  "Very High": "veryHigh",
};

export function TechnicalPlanReviewContent({
  review,
}: {
  review: PendingTechnicalPlanReview;
}) {
  const { t } = useTranslation();
  const renderLevel = (level: AssessmentLevel) =>
    t(`chat.assessmentLevels.${assessmentLevelKeys[level]}`);

  return (
    <>
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
    </>
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
