import { useTranslation } from "react-i18next";
import appPackage from "../../../package.json";
import { SelectMenu } from "../../components/overlay";
import type { AppLanguage } from "../../i18n";
import type { ThemePreference } from "../../theme/types";

type GeneralSettingsProps = {
  theme: ThemePreference;
  language: AppLanguage;
  onThemeChange: (theme: ThemePreference) => void;
  onLanguageChange: (language: AppLanguage) => void;
};

export function GeneralSettings({
  theme,
  language,
  onThemeChange,
  onLanguageChange,
}: GeneralSettingsProps) {
  const { t } = useTranslation();
  const themeOptions: { value: ThemePreference; label: string }[] = [
    { value: "day", label: t("settings.themeDay") },
    { value: "night", label: t("settings.themeNight") },
    { value: "system", label: t("settings.themeSystem") },
  ];
  const languageOptions: { value: AppLanguage; label: string }[] = [
    { value: "en", label: t("settings.english") },
    { value: "pt-BR", label: t("settings.portugueseBrazil") },
  ];

  return (
    <section className="settings-page" aria-label={t("settings.general")}>
      <section className="settings-group" aria-labelledby="application-title">
        <header className="settings-group-header">
          <h2 id="application-title">{t("settings.application")}</h2>
          <p>{t("settings.applicationDescription")}</p>
        </header>
        <div className="settings-setting-row">
          <strong>{t("settings.appVersion")}</strong>
          <span className="settings-setting-value">{appPackage.version}</span>
        </div>
      </section>

      <section className="settings-group" aria-labelledby="appearance-title">
        <header className="settings-group-header">
          <h2 id="appearance-title">{t("settings.appearance")}</h2>
          <p>{t("settings.appearanceDescription")}</p>
        </header>
        <div className="settings-settings-list">
          <div className="settings-setting-row">
            <strong>{t("settings.theme")}</strong>
            <SelectMenu
              value={theme}
              options={themeOptions}
              onChange={onThemeChange}
              label={t("settings.theme")}
            />
          </div>
          <div className="settings-setting-row">
            <strong>{t("settings.language")}</strong>
            <SelectMenu
              value={language}
              options={languageOptions}
              onChange={onLanguageChange}
              label={t("settings.language")}
            />
          </div>
        </div>
      </section>
    </section>
  );
}
