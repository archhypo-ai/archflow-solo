import { Activity, ArrowLeft, BookOpen, Bot, Cable, ChevronDown, Cpu, Puzzle, Server, Settings2, Wrench, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../../i18n";
import type { ThemePreference } from "../../../theme/types";
import { AgentSettings } from "./AgentSettings";
import { GeneralSettings } from "./GeneralSettings";
import { SkillsSettings } from "./SkillsSettings";
import { McpSettings } from "./McpSettings";
import { ToolsSettings } from "./ToolsSettings";
import { ModelsSettings } from "./ProviderSettings";
import { ObservabilitySettings } from "./ObservabilitySettings";
import { NavigationButton } from "../../../design-system";
import "./SettingsDialog.css";

type PluginSection = "skills" | "mcps" | "tools";
type SettingsSection = "general" | "agents" | "models" | "observability" | PluginSection;
type SettingsEntry = "general" | "agents" | "plugins" | "providers";
const LAST_PLUGIN_SECTION_KEY = "archhypo-flow-last-plugin-section";

function lastPluginSection(): PluginSection {
  try { const saved = localStorage.getItem(LAST_PLUGIN_SECTION_KEY); return saved === "mcps" || saved === "skills" ? saved : "tools"; }
  catch { return "tools"; }
}

type SettingsDialogProps = {
  open: boolean;
  initialSection?: SettingsEntry;
  theme: ThemePreference;
  language: AppLanguage;
  hitlEnabled: boolean;
  hitlSaveError: boolean;
  onHitlChange: (enabled: boolean) => void;
  globalContext: string;
  globalContextLoading: boolean;
  globalContextSaving: boolean;
  globalContextLoadError: boolean;
  onClose: () => void;
  onThemeChange: (theme: ThemePreference) => void;
  onLanguageChange: (language: AppLanguage) => void;
  onGlobalContextSave: (context: string) => Promise<void>;
};

export function SettingsDialog({
  open,
  initialSection = "general",
  theme,
  language,
  hitlEnabled,
  hitlSaveError,
  onHitlChange,
  globalContext,
  globalContextLoading,
  globalContextSaving,
  globalContextLoadError,
  onClose,
  onThemeChange,
  onLanguageChange,
  onGlobalContextSave,
}: SettingsDialogProps) {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState<SettingsSection>("general");
  const [pluginsExpanded, setPluginsExpanded] = useState(true);
  const [providersExpanded, setProvidersExpanded] = useState(true);
  const [observabilityDetail, setObservabilityDetail] = useState<{ id: "langfuse" | "langsmith"; name: string } | null>(null);
  const detail = activeSection === "observability" ? observabilityDetail : null;
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const ActiveSectionIcon = activeSection === "general" ? Settings2 : activeSection === "agents" ? Bot : activeSection === "models" ? Cpu : activeSection === "observability" ? Activity : activeSection === "skills" ? BookOpen : activeSection === "mcps" ? Cable : Wrench;
  const activeSectionTitle = t(`settings.${activeSection}`);

  function selectPluginSection(section: PluginSection) {
    setActiveSection(section);
    try { localStorage.setItem(LAST_PLUGIN_SECTION_KEY, section); } catch { /* Navigation still works without storage. */ }
  }

  useEffect(() => {
    if (!open) return;
    setObservabilityDetail(null);
    if (initialSection === "plugins") {
      setPluginsExpanded(true);
      setActiveSection(lastPluginSection());
    } else if (initialSection === "providers") {
      setProvidersExpanded(true);
      setActiveSection("models");
    } else setActiveSection(initialSection);
  }, [open, initialSection]);

  useEffect(() => {
    if (activeSection !== "observability") setObservabilityDetail(null);
  }, [activeSection]);

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
      className="settings-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      role="presentation"
    >
      <section
        className="settings-dialog"
        aria-labelledby="settings-dialog-title"
        aria-modal="true"
        role="dialog"
      >
        <aside className="settings-sidebar" aria-label={t("settings.navigation")}>
          <nav className="settings-nav" aria-label={t("settings.title")}>
            <button
              className={`settings-nav-item${activeSection === "general" ? " is-active" : ""}`}
              type="button"
              aria-current={activeSection === "general" ? "page" : undefined}
              onClick={() => setActiveSection("general")}
            >
              <Settings2 size={16} aria-hidden="true" />
              <span>{t("settings.general")}</span>
            </button>
            <button
              className={`settings-nav-item${activeSection === "agents" ? " is-active" : ""}`}
              type="button"
              aria-current={activeSection === "agents" ? "page" : undefined}
              onClick={() => setActiveSection("agents")}
            >
              <Bot size={16} aria-hidden="true" />
              <span>{t("settings.agents")}</span>
            </button>
            <button className="settings-nav-item settings-plugin-trigger" type="button" aria-expanded={providersExpanded} aria-controls="settings-provider-sections" onClick={() => {
              if (providersExpanded && (activeSection === "models" || activeSection === "observability")) setProvidersExpanded(false);
              else { setProvidersExpanded(true); setActiveSection("models"); }
            }}><Server size={16} aria-hidden="true" /><span>{t("settings.providers")}</span><ChevronDown size={15} className={providersExpanded ? "" : "is-collapsed"} aria-hidden="true" /></button>
            {providersExpanded && <div className="settings-plugin-sections" id="settings-provider-sections">
              <button className={`settings-nav-item settings-plugin-item${activeSection === "models" ? " is-active" : ""}`} type="button" aria-current={activeSection === "models" ? "page" : undefined} onClick={() => setActiveSection("models")}><Cpu size={16} aria-hidden="true" /><span>{t("settings.models")}</span></button>
              <button className={`settings-nav-item settings-plugin-item${activeSection === "observability" ? " is-active" : ""}`} type="button" aria-current={activeSection === "observability" ? "page" : undefined} onClick={() => setActiveSection("observability")}><Activity size={16} aria-hidden="true" /><span>{t("settings.observability")}</span></button>
            </div>}
            <button className="settings-nav-item settings-plugin-trigger" type="button" aria-expanded={pluginsExpanded} aria-controls="settings-plugin-sections" onClick={() => {
              if (pluginsExpanded && (activeSection === "skills" || activeSection === "mcps" || activeSection === "tools")) setPluginsExpanded(false);
              else { setPluginsExpanded(true); selectPluginSection(lastPluginSection()); }
            }}>
              <Puzzle size={16} aria-hidden="true" /><span>{t("settings.plugins")}</span><ChevronDown size={15} className={pluginsExpanded ? "" : "is-collapsed"} aria-hidden="true" />
            </button>
            {pluginsExpanded && <div className="settings-plugin-sections" id="settings-plugin-sections">
              <button className={`settings-nav-item settings-plugin-item${activeSection === "tools" ? " is-active" : ""}`} type="button" aria-current={activeSection === "tools" ? "page" : undefined} onClick={() => selectPluginSection("tools")}><Wrench size={16} aria-hidden="true" /><span>{t("settings.tools")}</span></button>
              <button className={`settings-nav-item settings-plugin-item${activeSection === "skills" ? " is-active" : ""}`} type="button" aria-current={activeSection === "skills" ? "page" : undefined} onClick={() => selectPluginSection("skills")}><BookOpen size={16} aria-hidden="true" /><span>{t("settings.skills")}</span></button>
              <button className={`settings-nav-item settings-plugin-item${activeSection === "mcps" ? " is-active" : ""}`} type="button" aria-current={activeSection === "mcps" ? "page" : undefined} onClick={() => selectPluginSection("mcps")}><Cable size={16} aria-hidden="true" /><span>{t("settings.mcps")}</span></button>
            </div>}
          </nav>
        </aside>

        <div className="settings-main">
          <header className="settings-main-header">
            {detail && <NavigationButton iconOnly icon={<ArrowLeft />}
              label={t("settingsPages.observability.back")} onClick={() => setObservabilityDetail(null)} />}
            <h1 id="settings-dialog-title" className="settings-main-title">
              {!detail && <ActiveSectionIcon size={18} aria-hidden="true" />}
              <span>{detail?.name ?? activeSectionTitle}</span>
            </h1>
            <button
              ref={closeButtonRef}
              className="settings-close-button"
              type="button"
              aria-label={t("settings.close")}
              title={t("settings.close")}
              onClick={onClose}
            >
              <X size={18} aria-hidden="true" />
            </button>
          </header>
          <div className="settings-content">
            {activeSection === "general" ? (
              <>
                <p className="settings-page-description">
                  {t("settings.description")}
                </p>
                <GeneralSettings
                  theme={theme}
                  language={language}
                  hitlEnabled={hitlEnabled}
                  hitlSaveError={hitlSaveError}
                  onHitlChange={onHitlChange}
                  onThemeChange={onThemeChange}
                  onLanguageChange={onLanguageChange}
                />
              </>
            ) : activeSection === "models" ? (
              <ModelsSettings />
            ) : activeSection === "observability" ? (
              <ObservabilitySettings selected={detail?.id ?? null} onSelect={setObservabilityDetail} />
            ) : activeSection === "skills" ? (
              <SkillsSettings />
            ) : activeSection === "mcps" ? (
              <McpSettings />
            ) : activeSection === "tools" ? (
              <ToolsSettings />
            ) : (
              <AgentSettings
                globalContext={globalContext}
                isLoading={globalContextLoading}
                isSaving={globalContextSaving}
                loadError={globalContextLoadError}
                onSave={onGlobalContextSave}
              />
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
