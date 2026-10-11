import { useEffect, useRef, useState } from "react";
import { Settings2, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../i18n";
import { GeneralSettings } from "./GeneralSettings";
import "./SettingsDialog.css";

type Theme = "day" | "night";
type SettingsSection = "general";

type SettingsDialogProps = {
  open: boolean;
  theme: Theme;
  language: AppLanguage;
  onClose: () => void;
  onThemeChange: (theme: Theme) => void;
  onLanguageChange: (language: AppLanguage) => void;
};

export function SettingsDialog({
  open,
  theme,
  language,
  onClose,
  onThemeChange,
  onLanguageChange,
}: SettingsDialogProps) {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState<SettingsSection>("general");
  const closeButtonRef = useRef<HTMLButtonElement>(null);

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
          </nav>
        </aside>

        <div className="settings-main">
          <header className="settings-main-header">
            <h1 id="settings-dialog-title" className="settings-main-title">
              <Settings2 size={18} aria-hidden="true" />
              <span>{t("settings.general")}</span>
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
            <p className="settings-page-description">{t("settings.description")}</p>
            {activeSection === "general" && (
              <GeneralSettings
                theme={theme}
                language={language}
                onThemeChange={onThemeChange}
                onLanguageChange={onLanguageChange}
              />
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
