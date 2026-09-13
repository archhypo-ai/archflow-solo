import { useI18n } from "../../../i18n";

export function AgentSettings() {
  const { t } = useI18n();

  return (
    <section className="settings-page" aria-labelledby="agent-settings-title">
      <header className="settings-page-header">
        <h2 id="agent-settings-title">{t("settings.agent")}</h2>
        <p>{t("settings.agentDescription")}</p>
      </header>

      <div className="settings-group">
        <div className="settings-group-header">
          <h3>{t("settings.execution")}</h3>
          <p>{t("settings.agentExecutionDescription")}</p>
        </div>
        <div className="settings-info-row">
          <div>
            <strong>{t("settings.rootAgent")}</strong>
            <span>{t("settings.rootAgentDescription")}</span>
          </div>
          <span className="settings-value">{t("settings.solo")}</span>
        </div>
      </div>
    </section>
  );
}
