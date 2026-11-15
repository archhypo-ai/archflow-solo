import { ArrowLeft, Eye, EyeOff, Search, Wrench } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import "./SkillsSettings.css";
import "./McpSettings.css";
import "./ToolsSettings.css";

type Tool = { id: "tavily" | "exa"; name: string; api_key_env: string; enabled: boolean; configured: boolean };
const API = "http://127.0.0.1:8765/api/tool-catalog";
const labels = {
  pt: { description: "Gerencie as ferramentas disponíveis.", search: "Buscar tools", searchDescription: "Pesquisa na web", back: "Voltar para Tools", configuration: "Configuração", key: "Chave de API", existing: "Chave configurada — digite para substituir", enter: "Insira a chave de API", envHint: "Também é possível usar a variável de ambiente", envPriority: "A chave salva tem prioridade.", save: "Salvar", saving: "Salvando...", saved: "Salvo.", error: "Não foi possível acessar a configuração da tool.", keyringError: "Não foi possível acessar o gerenciador de credenciais do sistema. Verifique se ele está disponível e desbloqueado.", loading: "Carregando...", empty: "Nenhuma tool encontrada.", configured: "Configurada", notConfigured: "Não configurada", disabled: "Desligada", enabled: "Ferramenta ligada", show: "Mostrar chave", hide: "Ocultar chave" },
  en: { description: "Manage available tools.", search: "Search tools", searchDescription: "Web search", back: "Back to Tools", configuration: "Configuration", key: "API key", existing: "Key configured — enter a new key to replace it", enter: "Enter API key", envHint: "You can also use the environment variable", envPriority: "The saved key takes precedence.", save: "Save", saving: "Saving...", saved: "Saved.", error: "Could not access the tool configuration.", keyringError: "Could not access the system credential store. Check that it is available and unlocked.", loading: "Loading...", empty: "No tools found.", configured: "Configured", notConfigured: "Not configured", disabled: "Disabled", enabled: "Tool enabled", show: "Show key", hide: "Hide key" },
};

export function ToolsSettings() {
  const { i18n } = useTranslation();
  const s = i18n.resolvedLanguage?.startsWith("pt") ? labels.pt : labels.en;
  const [tools, setTools] = useState<Tool[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [key, setKey] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [showKey, setShowKey] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const load = useCallback(async () => {
    try {
      const response = await fetch(API);
      if (!response.ok) throw new Error();
      setTools(await response.json() as Tool[]); setError("");
    } catch { setError(s.error); }
    finally { setLoading(false); }
  }, [s.error]);
  useEffect(() => { void load(); }, [load]);
  const current = tools.find((tool) => tool.id === selected);
  const filtered = tools.filter((tool) => tool.name.toLowerCase().includes(search.toLowerCase()));
  function status(tool: Tool) { return !tool.enabled ? s.disabled : tool.configured ? s.configured : s.notConfigured; }
  function open(tool: Tool) { setSelected(tool.id); setEnabled(tool.enabled); setKey(""); setShowKey(false); setSaved(false); setError(""); }
  async function save() {
    if (!current) return;
    setSaving(true); setError(""); setSaved(false);
    try {
      const response = await fetch(`${API}/${current.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled, ...(key.trim() ? { api_key: key.trim() } : {}) }) });
      if (!response.ok) { setError(response.status === 503 ? s.keyringError : s.error); return; }
      const updated = await response.json() as Tool;
      setTools((previous) => previous.map((tool) => tool.id === updated.id ? updated : tool));
      setKey(""); setShowKey(false); setSaved(true);
    } catch { setError(s.error); }
    finally { setSaving(false); }
  }
  return <div className="skills-page tools-page">
    {current ? <>
      <div className="mcp-detail-header"><button className="mcp-back" type="button" onClick={() => { setSelected(null); setKey(""); setError(""); }} aria-label={s.back} title={s.back}><ArrowLeft size={18} aria-hidden="true" /></button><div><h2>{current.name}</h2><p>{s.searchDescription}</p></div><span className={`mcp-status ${current.enabled && current.configured ? "is-connected" : "is-disconnected"}`}><span aria-hidden="true" />{status(current)}</span></div>
      <h3>{s.configuration}</h3>
      <div className="tools-toggle"><strong id="tool-enabled-label">{s.enabled}</strong><button className="settings-switch" type="button" role="switch" aria-checked={enabled} aria-labelledby="tool-enabled-label" onClick={() => { setEnabled(!enabled); setSaved(false); }}><span className="settings-switch-thumb" aria-hidden="true" /></button></div>
      <div className="tools-field"><label htmlFor="tool-api-key">{s.key}</label><div className="tools-key-input"><input id="tool-api-key" aria-describedby="tool-key-hint" type={showKey ? "text" : "password"} autoComplete="off" spellCheck={false} value={key} onChange={(event) => { setKey(event.target.value); setSaved(false); }} placeholder={current.configured ? s.existing : s.enter} /><button type="button" aria-label={showKey ? s.hide : s.show} title={showKey ? s.hide : s.show} onClick={() => setShowKey(!showKey)}>{showKey ? <EyeOff size={17} /> : <Eye size={17} />}</button></div><small id="tool-key-hint">{s.envHint} <code>{current.api_key_env}</code>. {s.envPriority}</small></div>
      <button type="button" className="skills-primary" onClick={() => void save()} disabled={saving}>{saving ? s.saving : s.save}</button>
      {saved && <p className="tools-saved" role="status">{s.saved}</p>}
    </> : <>
      <p className="settings-page-description">{s.description}</p>
      <div className="skills-toolbar"><div className="skills-search"><Search size={16} aria-hidden="true" /><input aria-label={s.search} placeholder={s.search} value={search} onChange={(event) => setSearch(event.target.value)} /></div></div>
      {loading ? <p className="skills-empty">{s.loading}</p> : !error && filtered.length === 0 ? <p className="skills-empty">{s.empty}</p> : <div className="skills-list">{filtered.map((tool) => <button type="button" className="skills-item" key={tool.id} onClick={() => open(tool)}><span className="skills-item-icon"><Wrench size={18} aria-hidden="true" /></span><span className="skills-item-content"><strong>{tool.name}</strong><span>{s.searchDescription}</span></span><span className={`mcp-status ${tool.enabled && tool.configured ? "is-connected" : "is-disconnected"}`}><span aria-hidden="true" />{status(tool)}</span></button>)}</div>}
    </>}
    {error && <p className="skills-error" role="alert">{error}</p>}
  </div>;
}
