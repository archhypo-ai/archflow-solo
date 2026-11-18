import { IconArchive as Archive, IconRefresh as RefreshCw, IconSearch as Search, IconX as X } from "@tabler/icons-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../../i18n";
import type { Project } from "../../projects/types";
import { useArtifacts } from "../hooks/useArtifacts";
import type { ArtifactSummary } from "../types";
import {
  ArtifactMultiSelectFilter,
  type ArtifactFilterOption,
} from "./ArtifactMultiSelectFilter";
import { ArtifactCard } from "./ArtifactCard";
import "./ArtifactsPage.css";

const NO_PROJECT_FILTER = "__no_project__";
const ASSESSMENT_LEVELS = ["Very Low", "Low", "Medium", "High", "Very High"];
const QUALITY_ATTRIBUTES = [
  "Performance",
  "Security",
  "Reliability",
  "Flexibility",
  "Usability",
  "Productivity",
];
const ASSESSMENT_LEVEL_TRANSLATIONS: Record<string, string> = {
  "Very Low": "veryLow",
  Low: "low",
  Medium: "medium",
  High: "high",
  "Very High": "veryHigh",
};

function ArtifactOverview({
  artifacts,
  onStatusSelect,
}: {
  artifacts: ArtifactSummary[];
  onStatusSelect: (status: string[]) => void;
}) {
  const { t } = useTranslation();
  const open = artifacts.filter(({ status }) => status === "open").length;
  const closed = artifacts.length - open;
  const levels = ASSESSMENT_LEVELS.map((level) => ({
    level,
    impact: artifacts.filter((item) => item.impact === level).length,
    uncertainty: artifacts.filter((item) => item.uncertaintyLevel === level).length,
  }));
  const max = Math.max(1, ...levels.flatMap(({ impact, uncertainty }) => [impact, uncertainty]));

  return (
    <section className="artifact-overview" aria-labelledby="artifact-overview-title">
      <h2 id="artifact-overview-title">{t("artifacts.overview.title")}</h2>
      <div className="artifact-overview-metrics">
        <button type="button" onClick={() => onStatusSelect([])}>
          <span>{t("artifacts.overview.total")}</span><strong>{artifacts.length}</strong>
        </button>
        <button type="button" onClick={() => onStatusSelect(["open"])}>
          <span>{t("artifacts.statusOpen")}</span><strong>{open}</strong>
        </button>
        <button type="button" onClick={() => onStatusSelect(["closed"])}>
          <span>{t("artifacts.statusClosed")}</span><strong>{closed}</strong>
        </button>
      </div>
      <div className="artifact-overview-charts">
        {(["impact", "uncertainty"] as const).map((metric) => (
          <section key={metric} className="artifact-overview-chart" aria-label={
            metric === "impact" ? t("artifacts.filters.impact") : t("artifacts.filters.uncertainty")
          }>
            <h3>{metric === "impact" ? t("artifacts.filters.impact") : t("artifacts.filters.uncertainty")}</h3>
            <ul>
              {levels.map((row) => (
                <li key={row.level}>
                  <span>{t(`chat.assessmentLevels.${ASSESSMENT_LEVEL_TRANSLATIONS[row.level]}`)}</span>
                  <span className="artifact-overview-track" aria-hidden="true">
                    <span style={{ width: `${row[metric] / max * 100}%` }} />
                  </span>
                  <span>{row[metric]}</span>
                </li>
              ))}
            </ul>
            <p>{t("artifacts.overview.unrated", {
              count: artifacts.length - levels.reduce((sum, row) => sum + row[metric], 0),
            })}</p>
          </section>
        ))}
      </div>
    </section>
  );
}

type ArtifactFilterKey = "status" | "project" | "impact" | "uncertainty" | "nfr";

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
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [selectedProjects, setSelectedProjects] = useState<string[]>([]);
  const [selectedImpacts, setSelectedImpacts] = useState<string[]>([]);
  const [selectedUncertainties, setSelectedUncertainties] = useState<string[]>([]);
  const [selectedQualityAttributes, setSelectedQualityAttributes] = useState<string[]>([]);
  const [openFilter, setOpenFilter] = useState<ArtifactFilterKey | null>(null);
  const projectNames = useMemo(
    () => new Map(projects.map((project) => [project.id, project.name])),
    [projects],
  );
  const statusOptions: ArtifactFilterOption[] = [
    { value: "open", label: t("artifacts.statusOpen") },
    { value: "closed", label: t("artifacts.statusClosed") },
  ];
  const projectOptions: ArtifactFilterOption[] = [
    ...projects.map((project) => ({ value: project.id, label: project.name })),
    ...(artifacts.some((artifact) => artifact.projectId === null)
      ? [{ value: NO_PROJECT_FILTER, label: t("artifacts.noProject") }]
      : []),
  ];
  const assessmentOptions = ASSESSMENT_LEVELS.map((level) => ({
    value: level,
    label: t(`chat.assessmentLevels.${ASSESSMENT_LEVEL_TRANSLATIONS[level]}`),
  }));
  const qualityAttributeOptions = QUALITY_ATTRIBUTES.map((attribute) => ({
    value: attribute,
    label: attribute,
  }));

  const hasActiveFilters = [
    selectedStatuses,
    selectedProjects,
    selectedImpacts,
    selectedUncertainties,
    selectedQualityAttributes,
  ].some((selection) => selection.length > 0);

  const filteredArtifacts = useMemo(
    () =>
      artifacts.filter(
        (artifact) =>
          (selectedStatuses.length === 0 ||
            selectedStatuses.includes(artifact.status)) &&
          (selectedProjects.length === 0 ||
            selectedProjects.includes(artifact.projectId ?? NO_PROJECT_FILTER)) &&
          (selectedImpacts.length === 0 ||
            (artifact.impact !== null && selectedImpacts.includes(artifact.impact))) &&
          (selectedUncertainties.length === 0 ||
            (artifact.uncertaintyLevel !== null &&
              selectedUncertainties.includes(artifact.uncertaintyLevel))) &&
          (selectedQualityAttributes.length === 0 ||
            (artifact.nfr !== null &&
              selectedQualityAttributes.includes(artifact.nfr))),
      ),
    [
      artifacts,
      selectedImpacts,
      selectedProjects,
      selectedQualityAttributes,
      selectedStatuses,
      selectedUncertainties,
    ],
  );

  const clearFilters = () => {
    setSelectedStatuses([]);
    setSelectedProjects([]);
    setSelectedImpacts([]);
    setSelectedUncertainties([]);
    setSelectedQualityAttributes([]);
    setOpenFilter(null);
  };

  const filterSelectAllLabel = t("artifacts.filters.selectAll");
  const filterClearLabel = t("artifacts.filters.clearSelection");
  const filterEmptyLabel = t("artifacts.filters.emptyOptions");

  return (
    <section className="artifacts-page" aria-labelledby="artifacts-heading">
      <div className="artifacts-page-inner">
        {!loading && !error && (
          <ArtifactOverview artifacts={artifacts} onStatusSelect={(statuses) => {
            clearFilters();
            setSelectedStatuses(statuses);
          }} />
        )}
        <header className="artifacts-page-header">
          {!loading && !error && artifacts.length > 0 && (
            <div
              className="artifact-filter-bar"
              aria-label={t("artifacts.filters.label")}
            >
              <ArtifactMultiSelectFilter
                label={t("artifacts.filters.status")}
                options={statusOptions}
                selectedValues={selectedStatuses}
                onChange={setSelectedStatuses}
                open={openFilter === "status"}
                onOpenChange={(open) => setOpenFilter(open ? "status" : null)}
                selectAllLabel={filterSelectAllLabel}
                clearLabel={filterClearLabel}
                emptyLabel={filterEmptyLabel}
              />
              <ArtifactMultiSelectFilter
                label={t("artifacts.filters.project")}
                options={projectOptions}
                selectedValues={selectedProjects}
                onChange={setSelectedProjects}
                open={openFilter === "project"}
                onOpenChange={(open) => setOpenFilter(open ? "project" : null)}
                selectAllLabel={filterSelectAllLabel}
                clearLabel={filterClearLabel}
                emptyLabel={filterEmptyLabel}
              />
              <ArtifactMultiSelectFilter
                label={t("artifacts.filters.impact")}
                options={assessmentOptions}
                selectedValues={selectedImpacts}
                onChange={setSelectedImpacts}
                open={openFilter === "impact"}
                onOpenChange={(open) => setOpenFilter(open ? "impact" : null)}
                selectAllLabel={filterSelectAllLabel}
                clearLabel={filterClearLabel}
                emptyLabel={filterEmptyLabel}
              />
              <ArtifactMultiSelectFilter
                label={t("artifacts.filters.uncertainty")}
                options={assessmentOptions}
                selectedValues={selectedUncertainties}
                onChange={setSelectedUncertainties}
                open={openFilter === "uncertainty"}
                onOpenChange={(open) => setOpenFilter(open ? "uncertainty" : null)}
                selectAllLabel={filterSelectAllLabel}
                clearLabel={filterClearLabel}
                emptyLabel={filterEmptyLabel}
              />
              <ArtifactMultiSelectFilter
                label={t("artifacts.filters.qualityAttribute")}
                options={qualityAttributeOptions}
                selectedValues={selectedQualityAttributes}
                onChange={setSelectedQualityAttributes}
                open={openFilter === "nfr"}
                onOpenChange={(open) => setOpenFilter(open ? "nfr" : null)}
                selectAllLabel={filterSelectAllLabel}
                clearLabel={filterClearLabel}
                emptyLabel={filterEmptyLabel}
              />
              {hasActiveFilters && (
                <button
                  className="artifact-filter-clear"
                  type="button"
                  onClick={clearFilters}
                >
                  <X size={14} aria-hidden="true" />
                  {t("artifacts.filters.clearAll")}
                </button>
              )}
            </div>
          )}
          {!loading && !error && (
            <span className="artifacts-count">
              {hasActiveFilters
                ? t("artifacts.filteredCount", {
                    count: filteredArtifacts.length,
                    total: artifacts.length,
                  })
                : t("artifacts.count", { count: artifacts.length })}
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
        ) : filteredArtifacts.length === 0 ? (
          <div className="artifacts-empty-state">
            <Search size={25} aria-hidden="true" />
            <h2>{t("artifacts.filters.noMatchesTitle")}</h2>
            <p>{t("artifacts.filters.noMatchesDescription")}</p>
            <button
              className="artifact-filter-clear-empty"
              type="button"
              onClick={clearFilters}
            >
              {t("artifacts.filters.clearAll")}
            </button>
          </div>
        ) : (
          <div className="artifacts-grid">
            {filteredArtifacts.map((artifact) => (
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
