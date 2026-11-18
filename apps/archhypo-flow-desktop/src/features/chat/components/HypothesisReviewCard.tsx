import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type {
  HypothesisReviewDecision,
  PendingHypothesisReview,
} from "../types";
import { HypothesisReviewContent } from "./HypothesisReviewContent";

type HypothesisReviewCardProps = {
  onDecision: (decision: HypothesisReviewDecision) => void;
  disabled?: boolean;
  review: PendingHypothesisReview;
};

export function isPendingHypothesisReview(
  value: unknown,
): value is PendingHypothesisReview {
  if (!value || typeof value !== "object" || !("kind" in value)) return false;
  if (value.kind !== "hypothesis_review" || !("hypothesis" in value)) {
    return false;
  }
  const hypothesis = value.hypothesis;
  return (
    !!hypothesis &&
    typeof hypothesis === "object" &&
    "uncertainty" in hypothesis &&
    typeof hypothesis.uncertainty === "string" &&
    "title" in hypothesis &&
    typeof hypothesis.title === "string" &&
    "statement" in hypothesis &&
    typeof hypothesis.statement === "string" &&
    "justification" in hypothesis &&
    typeof hypothesis.justification === "string"
  );
}

export function HypothesisReviewCard({ review, onDecision, disabled }: HypothesisReviewCardProps) {
  const { t } = useTranslation();
  const reasonId = useId();
  const [note, setNote] = useState("");
  const submit = onDecision;

  return (
    <section
      className="human-review-card"
      aria-label={t("chat.hypothesisReviewTitle")}
    >
      <HypothesisReviewContent hypothesis={review.hypothesis} />
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
                disabled={disabled || !note.trim()}
                onClick={() =>
                  submit({ decision: "rejected", reason: note.trim() })
                }
              >
                {t("chat.reviewReject")}
              </button>
              <button
                className="human-review-approve"
                disabled={disabled}
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

    </section>
  );
}
