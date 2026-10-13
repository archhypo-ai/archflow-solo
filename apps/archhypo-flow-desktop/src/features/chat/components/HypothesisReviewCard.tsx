import { useAui } from "@assistant-ui/react";
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type {
  HypothesisReviewDecision,
  PendingHypothesisReview,
} from "../types";
import { HypothesisReviewContent } from "./HypothesisReviewContent";

type HypothesisReviewCardProps = {
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

export function HypothesisReviewCard({ review }: HypothesisReviewCardProps) {
  const aui = useAui();
  const { t } = useTranslation();
  const reasonId = useId();
  const [note, setNote] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const submit = (decision: HypothesisReviewDecision) => {
    const text = decision.decision === "approved"
      ? [t("chat.hypothesisApprovedMessage"), decision.reason]
          .filter(Boolean)
          .join("\n\n")
      : decision.reason ?? "";
    aui.thread.append({
      role: "user",
      content: [{ type: "text", text }],
      metadata: { custom: { hypothesisReview: decision } },
      startRun: true,
    });
    setSubmitted(true);
  };

  return (
    <section
      className="hypothesis-review-card"
      aria-label={t("chat.hypothesisReviewTitle")}
    >
      <HypothesisReviewContent hypothesis={review.hypothesis} />
      {submitted ? (
        <p className="hypothesis-review-submitted" role="status">
          {t("chat.hypothesisReviewSubmitted")}
        </p>
      ) : (
        <>
          <div className="hypothesis-review-note-section">
            <div className="hypothesis-review-note-heading">
              <label className="hypothesis-review-note-label" htmlFor={reasonId}>
                {t("chat.reviewNoteLabel")}
              </label>
              <span className="hypothesis-review-note-hint">
                {t("chat.reviewNoteHint")}
              </span>
            </div>
            <textarea
              id={reasonId}
              className="hypothesis-review-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder={t("chat.rejectionReasonPlaceholder")}
              rows={2}
            />
          </div>
          <div className="hypothesis-review-footer">
            <div className="hypothesis-review-actions">
              <button
                className="hypothesis-review-reject"
                type="button"
                disabled={!note.trim()}
                onClick={() =>
                  submit({ decision: "rejected", reason: note.trim() })
                }
              >
                {t("chat.rejectHypothesis")}
              </button>
              <button
                className="hypothesis-review-approve"
                type="button"
                onClick={() =>
                  submit({
                    decision: "approved",
                    ...(note.trim() ? { reason: note.trim() } : {}),
                  })
                }
              >
                {t("chat.approveHypothesis")}
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
