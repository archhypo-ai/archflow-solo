import { X } from "lucide-react";
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
  const { t, i18n } = useTranslation();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const hypothesisNoteId = useId();
  const technicalPlanNoteId = useId();
  const samples = createReviewSamples(
    i18n.resolvedLanguage === "pt-BR" ? "pt-BR" : "en",
  );

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

function createReviewSamples(language: "en" | "pt-BR"): {
  hypothesis: PendingHypothesisReview;
  technicalPlan: PendingTechnicalPlanReview;
} {
  if (language === "pt-BR") {
    return {
      hypothesis: {
        kind: "hypothesis_review",
        hypothesis: {
          uncertainty:
            "A equipe ainda não sabe se a estratégia atual de persistência suporta o volume de escrita previsto sem degradar a experiência dos usuários.",
          title: "Validar a capacidade de escrita do armazenamento",
          statement:
            "A arquitetura de persistência atual sustenta o pico esperado de gravações sem ultrapassar o limite de latência acordado.",
          justification:
            "Essa hipótese é verificável com um teste de carga controlado antes de comprometer a equipe com uma mudança de arquitetura. O resultado permite comparar a capacidade atual com a demanda projetada e explicitar quando uma alternativa passa a ser necessária.",
        },
      },
      technicalPlan: {
        kind: "technical_plan_review",
        assessment: {
          impact: "High",
          impact_justification:
            "Uma degradação na persistência afeta diretamente operações essenciais e pode bloquear jornadas de usuários.",
          uncertainty: "Medium",
          uncertainty_justification:
            "Há métricas iniciais disponíveis, mas elas ainda não representam picos simultâneos de gravação.",
        },
        technical_plan: {
          rationale:
            "Medir o comportamento sob carga representativa antes de decidir se a arquitetura precisa mudar.",
          items: [
            {
              title: "Executar um experimento de carga controlado",
              objective:
                "Comparar latência e taxa de erro com os limites definidos para o produto.",
              description:
                "Reproduzir o pico esperado em um ambiente isolado, aumentando gradualmente a concorrência e registrando latência p95, saturação e erros de gravação.",
              pattern: "Architectural Spike",
              tradeoff:
                "Exige preparar dados e ambiente representativos, mas evita uma migração prematura.",
            },
            {
              title: "Definir um gatilho para reavaliar a persistência",
              objective:
                "Tornar explícito quando uma alternativa arquitetural será necessária.",
              description:
                "Documentar o limite de latência e a taxa de erro que acionam uma nova avaliação, incluindo quem acompanha as métricas após a implantação.",
              pattern: "Postpone Uncertain Decisions",
              tradeoff:
                "Adia a decisão estrutural, exigindo acompanhamento contínuo das métricas.",
            },
          ],
        },
      },
    };
  }

  return {
    hypothesis: {
      kind: "hypothesis_review",
      hypothesis: {
        uncertainty:
          "The team does not yet know whether the current persistence strategy can support the projected write volume without degrading the user experience.",
        title: "Validate the storage write capacity",
        statement:
          "The current persistence architecture supports the expected write peak without exceeding the agreed latency limit.",
        justification:
          "This hypothesis can be checked with a controlled load test before committing the team to an architectural change. The result compares current capacity with projected demand and makes the point at which an alternative is needed explicit.",
      },
    },
    technicalPlan: {
      kind: "technical_plan_review",
      assessment: {
        impact: "High",
        impact_justification:
          "Persistence degradation affects essential operations and can block user workflows.",
        uncertainty: "Medium",
        uncertainty_justification:
          "Initial metrics are available, but they do not yet represent simultaneous write peaks.",
      },
      technical_plan: {
        rationale:
          "Measure representative load behavior before deciding whether the architecture needs to change.",
        items: [
          {
            title: "Run a controlled load experiment",
            objective:
              "Compare latency and error rates against the product's agreed limits.",
            description:
              "Reproduce the expected peak in an isolated environment, gradually increase concurrency, and record p95 latency, saturation, and write errors.",
            pattern: "Architectural Spike",
            tradeoff:
              "Requires representative data and environment setup, but avoids a premature migration.",
          },
          {
            title: "Define a persistence reassessment trigger",
            objective:
              "Make it clear when an architectural alternative should be evaluated.",
            description:
              "Document the latency and error thresholds that trigger a new assessment, including who monitors the metrics after release.",
            pattern: "Postpone Uncertain Decisions",
            tradeoff:
              "Defers the structural decision and requires ongoing metric monitoring.",
          },
        ],
      },
    },
  };
}
