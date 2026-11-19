import { IconX as X } from "@tabler/icons-react";
import { useEffect, useId, useRef, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type {
  PendingHypothesisReview,
  PendingTechnicalPlanReview,
} from "../types";
import { ApprovedReviewSummary } from "./ApprovedReviewSummary";
import { HypothesisReviewContent } from "./HypothesisReviewContent";
import { TechnicalPlanReviewContent } from "./TechnicalPlanReviewContent";
import "./ReviewCardsPreviewDialog.css";

type ReviewCardsPreviewDialogProps = {
  open: boolean;
  onClose: () => void;
};

export function ReviewCardsPreviewDialog({
  open,
  onClose,
}: ReviewCardsPreviewDialogProps) {
  const { t } = useTranslation();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const hypothesisNoteId = useId();
  const technicalPlanNoteId = useId();
  const samples = t("reviewSamples", { returnObjects: true }) as {
    hypothesis: PendingHypothesisReview;
    technicalPlan: PendingTechnicalPlanReview;
  };

  useEffect(() => {
    if (!open) return;

    closeButtonRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);

  if (!open) return null;

  return (
    <div
      className="review-cards-preview-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      role="presentation"
    >
      <section
        className="review-cards-preview-dialog"
        aria-labelledby="review-cards-preview-title"
        aria-modal="true"
        role="dialog"
      >
        <header className="review-cards-preview-header">
          <div>
            <h1 id="review-cards-preview-title">
              {t("chat.reviewCardsPreviewTitle")}
            </h1>
            <p>{t("chat.reviewCardsPreviewDescription")}</p>
          </div>
          <button
            ref={closeButtonRef}
            className="review-cards-preview-close"
            type="button"
            aria-label={t("chat.closeReviewCardsPreview")}
            onClick={onClose}
          >
            <X size={19} aria-hidden="true" />
          </button>
        </header>

        <div className="review-cards-preview-content">
          <ReviewSampleGroup
            title={t("chat.hypothesisReviewTitle")}
          >
            <article className="review-preview-sample">
              <span className="review-preview-state is-pending">
                {t("chat.reviewPreviewPending")}
              </span>
              <section className="human-review-card">
                <HypothesisReviewContent
                  hypothesis={samples.hypothesis.hypothesis}
                />
                <PreviewNote id={hypothesisNoteId} />
                <PreviewActions />
              </section>
            </article>
            <article className="review-preview-sample">
              <span className="review-preview-state is-approved">
                {t("chat.reviewPreviewApproved")}
              </span>
              <ApprovedReviewSummary review={samples.hypothesis} />
            </article>
          </ReviewSampleGroup>

          <ReviewSampleGroup
            title={t("chat.technicalPlanReviewTitle")}
          >
            <article className="review-preview-sample">
              <span className="review-preview-state is-pending">
                {t("chat.reviewPreviewPending")}
              </span>
              <section className="human-review-card technical-plan-review-card">
                <TechnicalPlanReviewContent review={samples.technicalPlan} />
                <PreviewNote id={technicalPlanNoteId} />
                <PreviewActions />
              </section>
            </article>
            <article className="review-preview-sample">
              <span className="review-preview-state is-approved">
                {t("chat.reviewPreviewApproved")}
              </span>
              <ApprovedReviewSummary review={samples.technicalPlan} />
            </article>
          </ReviewSampleGroup>
        </div>
      </section>
    </div>
  );
}

function ReviewSampleGroup({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="review-preview-group">
      <h2>{title}</h2>
      <div className="review-preview-comparison">{children}</div>
    </section>
  );
}

function PreviewNote({ id }: { id: string }) {
  const { t } = useTranslation();
  return (
    <div className="human-review-note-section">
      <div className="human-review-note-heading">
        <label className="human-review-note-label" htmlFor={id}>
          {t("chat.reviewNoteLabel")}
        </label>
        <span className="human-review-note-hint">
          {t("chat.reviewNoteHint")}
        </span>
      </div>
      <textarea
        id={id}
        className="human-review-note"
        placeholder={t("chat.reviewReasonPlaceholder")}
        rows={2}
        readOnly
      />
    </div>
  );
}

function PreviewActions() {
  const { t } = useTranslation();
  return (
    <div className="human-review-footer">
      <div className="human-review-actions review-preview-actions">
        <button className="human-review-reject" type="button" disabled>
          {t("chat.reviewReject")}
        </button>
        <button className="human-review-approve" type="button" disabled>
          {t("chat.reviewApprove")}
        </button>
      </div>
    </div>
  );
}
