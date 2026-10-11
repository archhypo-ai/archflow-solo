import { useTranslation } from "react-i18next";

type AgentSettingsProps = {
  instructions: string;
  onInstructionsChange: (instructions: string) => void;
};

export function AgentSettings({
  instructions,
  onInstructionsChange,
}: AgentSettingsProps) {
  const { t } = useTranslation();

  return (
    <section className="settings-page agent-settings-page" aria-label={t("settings.agents")}>
      <header className="agent-settings-intro">
        <h2>{t("agents.instructionsTitle")}</h2>
        <p>{t("agents.subtitle")}</p>
      </header>
      <label className="visually-hidden" htmlFor="global-agent-instructions">
        {t("agents.instructionsTitle")}
      </label>
      <textarea
        id="global-agent-instructions"
        className="agent-instructions-editor"
        value={instructions}
        onChange={(event) => onInstructionsChange(event.target.value)}
        placeholder={t("agents.instructionsPlaceholder")}
        rows={10}
      />
    </section>
  );
}
