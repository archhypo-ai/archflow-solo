import { Switch } from "../../../design-system";
import { IconActivity as Activity, IconEye as Eye, IconEyeOff as EyeOff } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type en from "../../../i18n/locales/en.json";
import "./ObservabilitySettings.css";

type Provider = { id: "langfuse" | "langsmith"; name: string; enabled: boolean; configured: boolean; keys: Record<string, boolean> };
const API = "http://127.0.0.1:8765/api/providers/observability";
const fields = { langfuse: ["public_key", "secret_key"], langsmith: ["api_key"] } as const;

export function ObservabilitySettings({ selected, onSelect }: {
  selected: Provider["id"] | null;
  onSelect: (detail: Pick<Provider, "id" | "name">) => void;
}) {
  const { t } = useTranslation();
  const s = t("settingsPages.observability", { returnObjects: true }) as typeof en.settingsPages.observability;
  const [providers, setProviders] = useState<Provider[]>([]);
  const [enabled, setEnabled] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});
  const [shown, setShown] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(API, { signal: controller.signal }).then((response) => { if (!response.ok) throw new Error(); return response.json() as Promise<Provider[]>; }).then(setProviders).catch(() => { if (!controller.signal.aborted) setError(s.error); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [s.error]);
  const current = providers.find((provider) => provider.id === selected);
  function status(provider: Provider) { return !provider.enabled ? s.disabled : provider.configured ? s.configured : s.notConfigured; }
  function open(provider: Provider) { onSelect({ id: provider.id, name: provider.name }); setEnabled(provider.enabled); setValues({}); setShown({}); setError(""); setSaved(false); }
  async function save() {
    if (!current) return;
    setSaving(true); setError(""); setSaved(false);
    const keys = Object.fromEntries(Object.entries(values).filter(([, value]) => value.trim()).map(([field, value]) => [field, value.trim()]));
    try {
      const response = await fetch(`${API}/${current.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled, ...keys }) });
      if (!response.ok) { setError(response.status === 503 ? s.keyringError : s.error); return; }
      const updated = await response.json() as Provider;
      setProviders((previous) => previous.map((provider) => provider.id === updated.id ? updated : provider));
      setValues({}); setShown({}); setSaved(true);
    } catch { setError(s.error); }
    finally { setSaving(false); }
  }
  return <div className="observability-page settings-page">
    {current ? <>
      <div className="observability-detail-status"><span className={`mcp-status ${current.enabled && current.configured ? "is-connected" : "is-disconnected"}`}><span aria-hidden="true" />{status(current)}</span></div>
      <label className="observability-toggle" htmlFor="observability-enabled">
        <span>{s.enabled}</span>
        <Switch id="observability-enabled" aria-label={s.enabled} checked={enabled} onCheckedChange={(value) => { setEnabled(value); setSaved(false); }} />
      </label>
      {fields[current.id].map((field) => <div className="observability-field" key={field}>
        <label htmlFor={`obs-${field}`}>{field === "public_key" ? s.publicKey : field === "secret_key" ? s.secretKey : s.apiKey}</label>
        <div className="observability-key-input"><input id={`obs-${field}`} aria-describedby={`obs-${field}-hint`} type={shown[field] ? "text" : "password"} autoComplete="off" spellCheck={false} placeholder={current.keys[field] ? s.existing : s.enter} value={values[field] ?? ""} onChange={(event) => { setValues({ ...values, [field]: event.target.value }); setSaved(false); }} /><button type="button" aria-label={shown[field] ? s.hide : s.show} title={shown[field] ? s.hide : s.show} onClick={() => setShown({ ...shown, [field]: !shown[field] })}>{shown[field] ? <EyeOff size={17} /> : <Eye size={17} />}</button></div>
        <small id={`obs-${field}-hint`}>{s.hint} <code>{`${current.id}_${field}`.toUpperCase()}</code>. {s.precedence}</small>
      </div>)}
      <p className="observability-note">{s.optional} {s.restart}</p>
      <button type="button" className="observability-save" disabled={saving} onClick={() => void save()}>{saving ? s.saving : s.save}</button>
      {saved && <p className="observability-success" role="status">{s.saved}</p>}
    </> : <>
      <p className="settings-page-description">{s.description}</p>
      {loading ? <p className="observability-empty" role="status">{s.loading}</p> : error ? null : <div className="observability-list">
        {providers.map((provider) => <button type="button" className="observability-item" key={provider.id} onClick={() => open(provider)}>
          <span className="observability-item-icon"><Activity size={18} aria-hidden="true" /></span>
          <span className="observability-item-name">{provider.name}</span>
          <span className={`mcp-status ${provider.enabled && provider.configured ? "is-connected" : "is-disconnected"}`}><span aria-hidden="true" />{status(provider)}</span>
        </button>)}
      </div>}
    </>}
    {error && <p className="settings-inline-error" role="alert">{error}</p>}
  </div>;
}
