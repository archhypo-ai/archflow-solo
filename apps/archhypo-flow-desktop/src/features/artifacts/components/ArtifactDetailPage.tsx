import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
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
              {t("artifacts.idLabel", { id: artifact.id })}
            </code>
            {projectName && <span>{projectName}</span>}
            <time dateTime={artifact.createdAt}>
              {formatDate(artifact.createdAt, language)}
            </time>
          </div>
          <label className="artifact-status-control">
            <span>{t("artifacts.detail.status")}</span>
            <select
              value={artifact.status}
              disabled={statusSaving}
              onChange={(event) =>
                void handleStatusChange(event.currentTarget.value as ArtifactStatus)
              }
            >
              <option value="open">{t("artifacts.statusOpen")}</option>
              <option value="closed">{t("artifacts.statusClosed")}</option>
            </select>
          </label>
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
          <p className="artifact-detail-lead">{artifact.hypothesis.statement}</p>
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
          <div className="artifact-detail-plan-list">
            {artifact.technicalPlan.items.map((item, index) => (
              <article
                className="artifact-detail-plan-item"
                key={`${item.title}-${index}`}
              >
                <header>
                  <h3>{item.title}</h3>
                  <span>{item.pattern}</span>
                </header>
                <p>
                  <strong>{t("artifacts.detail.objective")}:</strong>{" "}
                  {item.objective}
                </p>
                <p>{item.description}</p>
                <p>
                  <strong>{t("artifacts.detail.tradeoff")}:</strong>{" "}
                  {item.tradeoff}
                </p>
              </article>
            ))}
          </div>
        </section>
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

function formatDate(value: string, language: AppLanguage): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(language, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}
