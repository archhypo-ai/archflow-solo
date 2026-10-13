import { CheckCircle2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import type {
  AssessmentLevel,
  PendingHumanReview,
} from "../types";
import "./HumanReviewCard.css";

const assessmentLevelKeys: Record<AssessmentLevel, string> = {
  "Very Low": "veryLow",
  Low: "low",
  Medium: "medium",
  High: "high",
  "Very High": "veryHigh",
};

export function ApprovedReviewSummary({
  review,
}: {
  review: PendingHumanReview;
}) {
  const { t } = useTranslation();
  const isHypothesisReview = review.kind === "hypothesis_review";

  return (
    <section
      className="human-review-card human-review-completed-card"
      aria-label={
        isHypothesisReview
          ? t("chat.completedHypothesisReview")
          : t("chat.completedTechnicalPlanReview")
      }
    >
      <div className="human-review-completed-heading">
        <CheckCircle2 aria-hidden="true" />
        <span>
          {isHypothesisReview
            ? t("chat.completedHypothesisReview")
            : t("chat.completedTechnicalPlanReview")}
        </span>
        <span className="human-review-completed-status">
          {t("chat.reviewApprovedStatus")}
        </span>
      </div>
      {isHypothesisReview ? (
        <p className="human-review-completed-summary">
          {review.hypothesis.title}
        </p>
      ) : (
        <>
          <div className="human-review-completed-levels">
            <CompletedLevel
              label={t("chat.impactLabel")}
              level={review.assessment.impact}
              translatedLevel={t(
                `chat.assessmentLevels.${assessmentLevelKeys[review.assessment.impact]}`,
              )}
            />
            <CompletedLevel
              label={t("chat.uncertaintyLabel")}
              level={review.assessment.uncertainty}
              translatedLevel={t(
                `chat.assessmentLevels.${assessmentLevelKeys[review.assessment.uncertainty]}`,
              )}
            />
          </div>
          <ul className="human-review-completed-plan-items">
            {review.technical_plan.items.map((item, index) => (
              <li key={`${index}-${item.title}`}>{item.title}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function CompletedLevel({
  label,
  level,
  translatedLevel,
}: {
  label: string;
  level: AssessmentLevel;
  translatedLevel: string;
}) {
  return (
    <span className="human-review-completed-level">
      <span>{label}</span>
      <span
        className="technical-plan-review-level"
        data-level={assessmentLevelKeys[level]}
      >
        {translatedLevel}
      </span>
    </span>
  );
}
