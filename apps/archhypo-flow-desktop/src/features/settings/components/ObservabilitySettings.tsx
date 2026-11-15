import { Activity, ArrowLeft, Eye, EyeOff } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import "./SkillsSettings.css";
import "./McpSettings.css";
import "./ToolsSettings.css";

type Provider = { id: "langfuse" | "langsmith"; name: string; enabled: boolean; configured: boolean; keys: Record<string, boolean> };
const API = "http://127.0.0.1:8765/api/providers/observability";
const labels = {
  pt: { description: "Gerencie os provedores de observabilidade.", back: "Voltar para Observability", configured: "Configurado", notConfigured: "Não configurado", disabled: "Desligado", enabled: "Provedor ligado", config: "Configuração", publicKey: "Chave pública", secretKey: "Chave secreta", apiKey: "Chave de API", existing: "Chave configurada — digite para substituir", enter: "Insira a chave", hint: "Também é possível usar a variável de ambiente", precedence: "A chave salva tem prioridade.", restart: "As alterações são aplicadas ao reiniciar o aplicativo.", saving: "Salvando...", save: "Salvar", saved: "Configuração salva.", error: "Não foi possível acessar a configuração.", keyringError: "Não foi possível acessar o gerenciador de credenciais do sistema. Verifique se está disponível e desbloqueado.", loading: "Carregando...", show: "Mostrar chave", hide: "Ocultar chave", optional: "Endpoint e projeto podem ser configurados por variáveis de ambiente." },
  en: { description: "Manage observability providers.", back: "Back to Observability", configured: "Configured", notConfigured: "Not configured", disabled: "Disabled", enabled: "Provider enabled", config: "Configuration", publicKey: "Public key", secretKey: "Secret key", apiKey: "API key", existing: "Key configured — enter a new key to replace it", enter: "Enter key", hint: "You can also use the environment variable", precedence: "The saved key takes precedence.", restart: "Changes take effect after restarting the application.", saving: "Saving...", save: "Save", saved: "Settings saved.", error: "Could not access provider settings.", keyringError: "Could not access the system credential store. Check that it is available and unlocked.", loading: "Loading...", show: "Show key", hide: "Hide key", optional: "Endpoint and project can be configured using environment variables." },
};
const fields = { langfuse: ["public_key", "secret_key"], langsmith: ["api_key"] } as const;

export function ObservabilitySettings() {
  const { i18n } = useTranslation();
  const s = i18n.resolvedLanguage?.startsWith("pt") ? labels.pt : labels.en;
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selected, setSelected] = useState<Provider["id"] | null>(null);
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
  function open(provider: Provider) { setSelected(provider.id); setEnabled(provider.enabled); setValues({}); setShown({}); setError(""); setSaved(false); }
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
  return <div className="skills-page tools-page">
    {current ? <>
      <div className="mcp-detail-header"><button className="mcp-back" type="button" onClick={() => { setSelected(null); setValues({}); setError(""); }} aria-label={s.back} title={s.back}><ArrowLeft size={18} aria-hidden="true" /></button><div><h2>{current.name}</h2></div><span className={`mcp-status ${current.enabled && current.configured ? "is-connected" : "is-disconnected"}`}><span aria-hidden="true" />{status(current)}</span></div>
      <div className="tools-toggle"><strong id="observability-enabled-label">{s.enabled}</strong><button className="settings-switch" type="button" role="switch" aria-checked={enabled} aria-labelledby="observability-enabled-label" onClick={() => { setEnabled(!enabled); setSaved(false); }}><span className="settings-switch-thumb" aria-hidden="true" /></button></div>
      {fields[current.id].map((field) => <div className="tools-field" key={field}><label htmlFor={`obs-${field}`}>{field === "public_key" ? s.publicKey : field === "secret_key" ? s.secretKey : s.apiKey}</label><div className="tools-key-input"><input id={`obs-${field}`} aria-describedby={`obs-${field}-hint`} type={shown[field] ? "text" : "password"} autoComplete="off" spellCheck={false} placeholder={current.keys[field] ? s.existing : s.enter} value={values[field] ?? ""} onChange={(event) => { setValues({ ...values, [field]: event.target.value }); setSaved(false); }} /><button type="button" aria-label={shown[field] ? s.hide : s.show} title={shown[field] ? s.hide : s.show} onClick={() => setShown({ ...shown, [field]: !shown[field] })}>{shown[field] ? <EyeOff size={17} /> : <Eye size={17} />}</button></div><small id={`obs-${field}-hint`}>{s.hint} <code>{`${current.id}_${field}`.toUpperCase()}</code>. {s.precedence}</small></div>)}
      <p className="provider-hint">{s.optional} {s.restart}</p>
      <button type="button" className="skills-primary" disabled={saving} onClick={() => void save()}>{saving ? s.saving : s.save}</button>
      {saved && <p className="tools-saved" role="status">{s.saved}</p>}
    </> : <><p className="settings-page-description">{s.description}</p>{loading ? <p className="skills-empty">{s.loading}</p> : <div className="skills-list">{providers.map((provider) => <button type="button" className="skills-item" key={provider.id} onClick={() => open(provider)}><span className="skills-item-icon"><Activity size={18} aria-hidden="true" /></span><span className="skills-item-content"><strong>{provider.name}</strong></span><span className={`mcp-status ${provider.enabled && provider.configured ? "is-connected" : "is-disconnected"}`}><span aria-hidden="true" />{status(provider)}</span></button>)}</div>}</>}
    {error && <p className="skills-error" role="alert">{error}</p>}
  </div>;
}
