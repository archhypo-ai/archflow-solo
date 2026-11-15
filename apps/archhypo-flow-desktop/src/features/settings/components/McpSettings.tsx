import { FolderOpen, Plus, Search } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import "./SkillsSettings.css";

export function McpSettings() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");

  return (
    <div className="skills-page">
      <p className="settings-page-description">{t("settings.mcpDescription")}</p>
      <div className="skills-toolbar">
        <div className="skills-search">
          <Search size={16} aria-hidden="true" />
          <input
            aria-label={t("settings.mcpSearch")}
            placeholder={t("settings.mcpSearch")}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className="skills-toolbar-actions">
          <button className="skills-folder-button" type="button" disabled title={t("settings.mcpComingSoon")}>
            <FolderOpen size={16} aria-hidden="true" /> {t("settings.mcpFolder")}
          </button>
          <button className="skills-primary" type="button" disabled title={t("settings.mcpComingSoon")}>
            <Plus size={16} aria-hidden="true" /> {t("settings.mcpAdd")}
          </button>
        </div>
      </div>
      <p className="skills-empty">{t("settings.mcpEmpty")}</p>
      <p className="mcp-placeholder-note">{t("settings.mcpComingSoon")}</p>
    </div>
  );
}
