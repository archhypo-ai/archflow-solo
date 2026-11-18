import { IconRefresh as RefreshCw } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SelectMenu } from "../../../components/overlay";
import type { AppLanguage } from "../../../i18n";
import { getArtifact, updateArtifactStatus } from "../api/artifactClient";
import type { ArtifactDetail, ArtifactStatus } from "../types";
import "./ArtifactDetailPage.css";

type ArtifactDetailPageProps = {
  artifactId: string;
  projectName: string | null;
  language: AppLanguage;
};

const assessmentLevelKeys: Record<string, string> = {
  "Very Low": "veryLow",
  Low: "low",
  Medium: "medium",
  High: "high",
  "Very High": "veryHigh",
};

export function ArtifactDetailPage({
  artifactId,
  projectName,
  language,
}: ArtifactDetailPageProps) {
  const { t } = useTranslation();
  const statusOptions = [
    { value: "open" as const, label: t("artifacts.statusOpen") },
    { value: "closed" as const, label: t("artifacts.statusClosed") },
  ];
  const [artifact, setArtifact] = useState<ArtifactDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [statusSaving, setStatusSaving] = useState(false);
  const [statusError, setStatusError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError(false);
    void getArtifact(artifactId)
      .then((loadedArtifact) => {
        if (active) setArtifact(loadedArtifact);
      })
      .catch((error: unknown) => {
        console.error("Could not load ArchHypo artifact details", error);
        if (active) setLoadError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [artifactId, reloadKey]);

  const handleStatusChange = async (status: ArtifactStatus) => {
    if (!artifact || statusSaving || status === artifact.status) return;
    setStatusSaving(true);
    setStatusError(false);
    try {
      setArtifact(await updateArtifactStatus(artifact.id, status));
    } catch (error) {
      console.error("Could not update ArchHypo artifact status", error);
      setStatusError(true);
    } finally {
      setStatusSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="artifact-detail-state" role="status">
        {t("artifacts.detail.loading")}
      </div>
    );
  }

  if (loadError || !artifact) {
    return (
      <div className="artifact-detail-state is-error" role="alert">
        <p>{t("artifacts.detail.loadError")}</p>
        <button type="button" onClick={() => setReloadKey((key) => key + 1)}>
          <RefreshCw size={15} aria-hidden="true" />
          {t("artifacts.retry")}
        </button>
      </div>
    );
  }

  const renderLevel = (level: string) => {
    const key = assessmentLevelKeys[level];
    return key ? t(`chat.assessmentLevels.${key}`) : level;
  };

  return (
    <section className="artifact-detail-page">
      <div className="artifact-detail-inner">
        <header className="artifact-detail-toolbar">
          <div className="artifact-detail-metadata">
            <code title={artifact.id}>
              {t("artifacts.idLabel", { id: artifact.id.slice(0, 8) })}
            </code>
            {projectName && <span>{projectName}</span>}
            <time dateTime={artifact.createdAt}>
              {formatDate(artifact.createdAt, language)}
            </time>
          </div>
          <div className="artifact-status-control">
            <span>{t("artifacts.detail.status")}</span>
            <SelectMenu
              value={artifact.status}
              options={statusOptions}
              label={t("artifacts.detail.status")}
              disabled={statusSaving}
              onChange={(status) => void handleStatusChange(status)}
            />
          </div>
        </header>
        {statusSaving && (
          <p className="artifact-status-feedback" role="status">
            {t("artifacts.detail.statusSaving")}
          </p>
        )}
        {statusError && (
          <p className="artifact-status-feedback is-error" role="alert">
            {t("artifacts.detail.statusError")}
          </p>
        )}

        <section className="artifact-detail-section">
          <h2>{t("artifacts.detail.uncertainty")}</h2>
          <p className="artifact-detail-lead">{artifact.uncertainty}</p>
        </section>

        <section className="artifact-detail-section">
          <h2>{t("artifacts.detail.hypothesis")}</h2>
          <p className="artifact-detail-lead">
            {artifact.hypothesis.statement}
          </p>
          {artifact.hypothesis.justification && (
            <p className="artifact-detail-copy">
              {artifact.hypothesis.justification}
            </p>
          )}
        </section>

        <section className="artifact-detail-section">
          <h2>{t("artifacts.detail.assessment")}</h2>
          <div className="artifact-detail-assessments">
            <AssessmentCard
              label={t("artifacts.detail.nfr")}
              value={artifact.assessment.nfr}
              justification={artifact.assessment.nfrJustification}
            />
            <AssessmentCard
              label={t("chat.impactLabel")}
              value={artifact.assessment.impact}
              levelKey={assessmentLevelKeys[artifact.assessment.impact]}
              justification={artifact.assessment.impactJustification}
              translatedValue={renderLevel(artifact.assessment.impact)}
            />
            <AssessmentCard
              label={t("chat.uncertaintyLabel")}
              value={artifact.assessment.uncertainty}
              levelKey={assessmentLevelKeys[artifact.assessment.uncertainty]}
              justification={artifact.assessment.uncertaintyJustification}
              translatedValue={renderLevel(artifact.assessment.uncertainty)}
            />
          </div>
        </section>

        <section className="artifact-detail-section">
          <h2>{t("artifacts.detail.technicalPlan")}</h2>
          {artifact.technicalPlan.rationale && (
            <p className="artifact-detail-copy">
              {artifact.technicalPlan.rationale}
            </p>
          )}
          <ol className="artifact-detail-plan-list">
            {artifact.technicalPlan.items.map((item, index) => (
              <li
                className="artifact-detail-plan-item"
                key={`${item.title}-${index}`}
              >
                <div className="artifact-detail-plan-heading">
                  <span className="artifact-detail-plan-number">
                    {index + 1}
                  </span>
                  <div className="artifact-detail-plan-title">
                    <h3>{item.title}</h3>
                    <span className="artifact-detail-pattern">
                      {item.pattern}
                    </span>
                  </div>
                </div>
                {item.objective && (
                  <PlanField
                    label={t("chat.planObjectiveLabel")}
                    value={item.objective}
                  />
                )}
                {item.description && (
                  <PlanField
                    label={t("chat.planDescriptionLabel")}
                    value={item.description}
                  />
                )}
                {item.tradeoff && (
                  <PlanField
                    label={t("chat.planTradeoffLabel")}
                    value={item.tradeoff}
                  />
                )}
              </li>
            ))}
          </ol>
        </section>

        {artifact.reviewHistory.length > 0 && (
          <section className="artifact-detail-section">
            <h2>{t("artifacts.detail.reviewHistory")}</h2>
            <ol className="artifact-detail-review-list">
              {artifact.reviewHistory.map((entry, index) => {
                const isHypothesisReview = entry.kind === "hypothesis_review";
                const isApproved = entry.decision.decision === "approved";
                const candidateTitle = isHypothesisReview
                  ? entry.review.hypothesis?.title
                  : undefined;
                const candidateSummary = isHypothesisReview
                  ? entry.review.hypothesis?.statement
                  : entry.review.technical_plan?.rationale;
                const planItemTitles = isHypothesisReview
                  ? []
                  : (entry.review.technical_plan?.items ?? [])
                      .map((item) => item.title)
                      .filter((title): title is string => Boolean(title));
                const reason = entry.decision.reason?.trim();

                return (
                  <li
                    className="artifact-detail-review-entry"
                    key={`${entry.kind}-${index}`}
                  >
                    <article className="artifact-detail-review-card">
                      <header>
                        <div className="artifact-detail-review-heading">
                          <span className="artifact-detail-review-number">
                            {index + 1}
                          </span>
                          <h3>
                            {t(
                              isHypothesisReview
                                ? "artifacts.detail.hypothesisReview"
                                : "artifacts.detail.technicalPlanReview",
                            )}
                          </h3>
                        </div>
                        <span
                          className={`artifact-detail-review-decision ${isApproved ? "is-approved" : "is-rejected"}`}
                        >
                          {t(
                            isApproved
                              ? "artifacts.detail.reviewApproved"
                              : "artifacts.detail.reviewRejected",
                          )}
                        </span>
                      </header>
                      {candidateTitle && (
                        <h4 className="artifact-detail-review-candidate-title">
                          {candidateTitle}
                        </h4>
                      )}
                      {candidateSummary && (
                        <p className="artifact-detail-review-candidate-summary">
                          {candidateSummary}
                        </p>
                      )}
                      {planItemTitles.length > 0 && (
                        <ul className="artifact-detail-review-plan-items">
                          {planItemTitles.map((title, itemIndex) => (
                            <li key={`${itemIndex}-${title}`}>{title}</li>
                          ))}
                        </ul>
                      )}
                      {reason && (
                        <div className="artifact-detail-review-note">
                          <span>{t("artifacts.detail.reviewNote")}</span>
                          <p>{reason}</p>
                        </div>
                      )}
                    </article>
                  </li>
                );
              })}
            </ol>
          </section>
        )}
      </div>
    </section>
  );
}

function AssessmentCard({
  label,
  value,
  levelKey,
  translatedValue,
  justification,
}: {
  label: string;
  value: string;
  levelKey?: string;
  translatedValue?: string;
  justification: string;
}) {
  return (
    <article className="artifact-detail-assessment">
      <header>
        <h3>{label}</h3>
        {levelKey ? (
          <span className="artifact-detail-level" data-level={levelKey}>
            {translatedValue ?? value}
          </span>
        ) : (
          <span className="artifact-detail-nfr">{value}</span>
        )}
      </header>
      <p>{justification}</p>
    </article>
  );
}

function PlanField({ label, value }: { label: string; value: string }) {
  return (
    <div className="artifact-detail-plan-field">
      <span>{label}</span>
      <p>{value}</p>
    </div>
  );
}

function formatDate(value: string, language: AppLanguage): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(language, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}
