import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../../i18n";
import type { ArtifactSummary } from "../types";

type ArtifactCardProps = {
  artifact: ArtifactSummary;
  projectName: string | null;
  language: AppLanguage;
  onSelect: (artifact: ArtifactSummary) => void;
};

export function ArtifactCard({
  artifact,
  projectName,
  language,
  onSelect,
}: ArtifactCardProps) {
  const { t } = useTranslation();
  const status = artifact.status.toLowerCase();
  const statusLabel =
    status === "open"
      ? t("artifacts.statusOpen")
      : status === "closed"
        ? t("artifacts.statusClosed")
        : formatEnum(artifact.status);
  const translatedLevel = (value: string) => {
    const key = assessmentLevelKeys[value];
    return key ? t(`chat.assessmentLevels.${key}`) : value;
  };
  const planPatterns = [
    ...new Set(artifact.technicalPlanItems.map((item) => item.pattern)),
  ];

  return (
    <article
      className="artifact-card"
      role="button"
      tabIndex={0}
      aria-label={t("artifacts.openArtifact", { title: artifact.title })}
      onClick={() => onSelect(artifact)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(artifact);
        }
      }}
    >
      <header className="artifact-card-header">
        <span className={`artifact-status-badge is-${status}`}>
          {statusLabel}
        </span>
        <time className="artifact-date" dateTime={artifact.createdAt}>
          {formatDate(artifact.createdAt, language)}
        </time>
      </header>

      <h2 className="artifact-card-title" title={artifact.title}>
        {artifact.title}
      </h2>

      <div className="artifact-card-identity">
        <code title={artifact.id}>
          {t("artifacts.idLabel", { id: artifact.id.slice(0, 8) })}
        </code>
        <span className="artifact-project-label" title={projectName ?? undefined}>
          {projectName ?? t("artifacts.noProject")}
        </span>
      </div>

      <div className="artifact-assessment-badges">
        {artifact.nfr && (
          <span className="artifact-tag is-nfr">{artifact.nfr}</span>
        )}
        {artifact.impact && (
          <span className="artifact-assessment-level">
            <span>{t("chat.impactLabel")}</span>
            <span
              className="artifact-level-badge"
              data-level={assessmentLevelKey(artifact.impact)}
            >
              {translatedLevel(artifact.impact)}
            </span>
          </span>
        )}
        {artifact.uncertaintyLevel && (
          <span className="artifact-assessment-level">
            <span>{t("chat.uncertaintyLabel")}</span>
            <span
              className="artifact-level-badge"
              data-level={assessmentLevelKey(artifact.uncertaintyLevel)}
            >
              {translatedLevel(artifact.uncertaintyLevel)}
            </span>
          </span>
        )}
      </div>

      {planPatterns.length > 0 && (
        <section className="artifact-plans" aria-label={t("artifacts.plansLabel")}>
          <h3>{t("artifacts.plansLabel")}</h3>
          <div className="artifact-plan-badges">
            {planPatterns.map((pattern) => (
              <span className="artifact-plan-badge" key={pattern}>
                {pattern}
              </span>
            ))}
          </div>
        </section>
      )}
    </article>
  );
}

const assessmentLevelKeys: Record<string, string> = {
  "Very Low": "veryLow",
  Low: "low",
  Medium: "medium",
  High: "high",
  "Very High": "veryHigh",
};

function assessmentLevelKey(value: string): string {
  return assessmentLevelKeys[value] ?? "medium";
}

function formatEnum(value: string): string {
  return value.replace(/_/g, " ");
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
