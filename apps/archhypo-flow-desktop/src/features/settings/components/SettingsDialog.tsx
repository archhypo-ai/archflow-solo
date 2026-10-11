import { Bot, Settings2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../../i18n";
import type { ThemePreference } from "../../../theme/types";
import { AgentSettings } from "./AgentSettings";
import { GeneralSettings } from "./GeneralSettings";
import "./SettingsDialog.css";

type SettingsSection = "general" | "agents";

type SettingsDialogProps = {
  open: boolean;
  theme: ThemePreference;
  language: AppLanguage;
  globalAgentInstructions: string;
  onClose: () => void;
  onThemeChange: (theme: ThemePreference) => void;
  onLanguageChange: (language: AppLanguage) => void;
  onGlobalAgentInstructionsChange: (instructions: string) => void;
};

export function SettingsDialog({
  open,
  theme,
  language,
  globalAgentInstructions,
  onClose,
  onThemeChange,
  onLanguageChange,
  onGlobalAgentInstructionsChange,
}: SettingsDialogProps) {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState<SettingsSection>("general");
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const ActiveSectionIcon = activeSection === "general" ? Settings2 : Bot;
  const activeSectionTitle = t(
    activeSection === "general" ? "settings.general" : "settings.agents",
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
          </nav>
        </aside>

        <div className="settings-main">
          <header className="settings-main-header">
            <h1 id="settings-dialog-title" className="settings-main-title">
              <ActiveSectionIcon size={18} aria-hidden="true" />
              <span>{activeSectionTitle}</span>
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
                  onThemeChange={onThemeChange}
                  onLanguageChange={onLanguageChange}
                />
              </>
            ) : (
              <AgentSettings
                instructions={globalAgentInstructions}
                onInstructionsChange={onGlobalAgentInstructionsChange}
              />
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
