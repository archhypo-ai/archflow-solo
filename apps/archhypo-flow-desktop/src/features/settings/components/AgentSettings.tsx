import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

type AgentSettingsProps = {
  globalContext: string;
  isLoading: boolean;
  isSaving: boolean;
  loadError: boolean;
  onSave: (context: string) => Promise<void>;
};

export function AgentSettings({
  globalContext,
  isLoading,
  isSaving,
  loadError,
  onSave,
}: AgentSettingsProps) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState(globalContext);
  const [saveError, setSaveError] = useState(false);

  useEffect(() => setDraft(globalContext), [globalContext]);

  const handleSave = async () => {
    setSaveError(false);
    try {
      await onSave(draft);
    } catch {
      setSaveError(true);
    }
  };

  return (
    <section className="settings-page agent-settings-page" aria-label={t("settings.agents")}>
      <header className="agent-settings-intro">
        <h2>{t("agents.contextTitle")}</h2>
        <p>{t("agents.contextDescription")}</p>
      </header>
      <label className="visually-hidden" htmlFor="global-agent-context">
        {t("agents.contextTitle")}
      </label>
      <textarea
        id="global-agent-context"
        className="agent-instructions-editor"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        placeholder={t("agents.contextPlaceholder")}
        rows={10}
        disabled={isLoading || isSaving}
      />
      {loadError && <p className="settings-inline-error" role="alert">{t("agents.loadError")}</p>}
      {saveError && <p className="settings-inline-error" role="alert">{t("agents.saveError")}</p>}
      <div className="agent-settings-actions">
        <button
          className="agent-settings-save"
          type="button"
          disabled={isLoading || isSaving || (!loadError && draft === globalContext)}
          onClick={() => void handleSave()}
        >
          {isSaving ? t("agents.saving") : t("agents.save")}
        </button>
      </div>
    </section>
  );
}
