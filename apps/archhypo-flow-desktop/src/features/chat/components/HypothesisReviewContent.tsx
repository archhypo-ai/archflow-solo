import { ChevronRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { PendingHypothesisReview } from "../types";
import "./HypothesisReviewCard.css";

type HypothesisReviewContentProps = {
  hypothesis: PendingHypothesisReview["hypothesis"];
  rationaleInitiallyOpen?: boolean;
};

function rationaleParagraphs(text: string): string[] {
  const paragraphs = text
    .trim()
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  if (paragraphs.length > 1) return paragraphs;

  return (paragraphs[0] ?? "").split(/(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ])/u);
}

export function HypothesisReviewContent({
  hypothesis,
  rationaleInitiallyOpen = false,
}: HypothesisReviewContentProps) {
  const { t } = useTranslation();

  return (
    <>
      <div className="hypothesis-review-context">
        <span className="hypothesis-review-label">
          {t("chat.hypothesisContextLabel")}
        </span>
        <p>{hypothesis.uncertainty}</p>
      </div>

      <div className="hypothesis-review-hypothesis">
        <span className="hypothesis-review-label">
          {t("chat.hypothesisLabel")}
        </span>
        <h3>{hypothesis.title}</h3>
        <p>{hypothesis.statement}</p>
      </div>

      <details
        className="hypothesis-review-rationale"
        open={rationaleInitiallyOpen || undefined}
      >
        <summary>
          <ChevronRight
            className="hypothesis-review-rationale-chevron"
            aria-hidden="true"
          />
          <span>{t("chat.hypothesisRationaleLabel")}</span>
        </summary>
        <div className="hypothesis-review-rationale-copy">
          {rationaleParagraphs(hypothesis.justification).map((paragraph, index) => (
            <p key={`${index}-${paragraph.slice(0, 24)}`}>{paragraph}</p>
          ))}
        </div>
      </details>
    </>
  );
}
