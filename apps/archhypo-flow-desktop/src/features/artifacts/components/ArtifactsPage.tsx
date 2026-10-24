import { Archive, RefreshCw } from "lucide-react";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../../i18n";
import type { Project } from "../../projects/types";
import { useArtifacts } from "../hooks/useArtifacts";
import type { ArtifactSummary } from "../types";
import { ArtifactCard } from "./ArtifactCard";
import "./ArtifactsPage.css";

type ArtifactsPageProps = {
  language: AppLanguage;
  projects: Project[];
  onArtifactSelect: (artifact: ArtifactSummary) => void;
};

export function ArtifactsPage({
  language,
  projects,
  onArtifactSelect,
}: ArtifactsPageProps) {
  const { t } = useTranslation();
  const { artifacts, loading, error, reload } = useArtifacts();
  const projectNames = useMemo(
    () => new Map(projects.map((project) => [project.id, project.name])),
    [projects],
  );

  return (
    <section className="artifacts-page" aria-labelledby="artifacts-heading">
      <div className="artifacts-page-inner">
        <header className="artifacts-page-header">
          {!loading && !error && (
            <span className="artifacts-count">
              {t("artifacts.count", { count: artifacts.length })}
            </span>
          )}
        </header>

        {loading ? (
          <div className="artifacts-state" role="status">
            {t("artifacts.loading")}
          </div>
        ) : error ? (
          <div className="artifacts-state is-error" role="alert">
            <p>{t("artifacts.loadError")}</p>
            <button type="button" onClick={() => void reload()}>
              <RefreshCw size={15} aria-hidden="true" />
              {t("artifacts.retry")}
            </button>
          </div>
        ) : artifacts.length === 0 ? (
          <div className="artifacts-empty-state">
            <Archive size={25} aria-hidden="true" />
            <h2>{t("artifacts.emptyTitle")}</h2>
            <p>{t("artifacts.emptyDescription")}</p>
          </div>
        ) : (
          <div className="artifacts-grid">
            {artifacts.map((artifact) => (
              <ArtifactCard
                artifact={artifact}
                key={artifact.id}
                language={language}
                onSelect={onArtifactSelect}
                projectName={
                  artifact.projectId
                    ? projectNames.get(artifact.projectId) ?? null
                    : null
                }
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
