import { SelectMenu } from "../../../components/overlay";
import { useI18n, type Language } from "../../../i18n";
import { useTheme } from "../../theme";
import type { AppearancePreference } from "../types";

export function GeneralSettings() {
  const { language, setLanguage, t } = useI18n();
  const { appearance, setAppearance } = useTheme();

  const appearanceOptions: readonly {
    value: AppearancePreference;
    label: string;
  }[] = [
    { value: "system", label: t("settings.system") },
    { value: "light", label: t("settings.light") },
    { value: "dark", label: t("settings.dark") },
  ];
  const languageOptions: readonly { value: Language; label: string }[] = [
    { value: "en", label: t("settings.english") },
    { value: "pt-BR", label: t("settings.portuguese") },
  ];

  return (
    <section className="settings-page" aria-labelledby="general-settings-title">
      <header className="settings-page-header">
        <h2 id="general-settings-title">{t("settings.general")}</h2>
        <p>{t("settings.generalDescription")}</p>
      </header>

      <div className="settings-settings-list">
        <div className="settings-setting-row">
          <div className="settings-setting-copy">
            <h3>{t("settings.appearance")}</h3>
            <p>{t("settings.appearanceDescription")}</p>
          </div>
          <SelectMenu
            label={t("settings.appearance")}
            onChange={setAppearance}
            options={appearanceOptions}
            value={appearance}
          />
        </div>

        <div className="settings-setting-row">
          <div className="settings-setting-copy">
            <h3>{t("settings.language")}</h3>
            <p>{t("settings.languageDescription")}</p>
          </div>
          <SelectMenu
            label={t("settings.language")}
            onChange={setLanguage}
            options={languageOptions}
            value={language}
          />
        </div>
      </div>
    </section>
  );
}
