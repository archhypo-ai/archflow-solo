import { NavigationButton, Switch } from "../../../design-system";
import { IconArrowLeft as ArrowLeft, IconEye as Eye, IconEyeOff as EyeOff, IconSearch as Search, IconTool as Wrench } from "@tabler/icons-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type en from "../../../i18n/locales/en.json";
import "./SkillsSettings.css";
import "./McpSettings.css";
import "./ToolsSettings.css";

type Tool = { id: "tavily" | "exa"; name: string; api_key_env: string; enabled: boolean; configured: boolean };
const API = "http://127.0.0.1:8765/api/tool-catalog";

export function ToolsSettings() {
  const { t } = useTranslation();
  const s = t("settingsPages.tools", { returnObjects: true }) as typeof en.settingsPages.tools;
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
      <div className="mcp-detail-header"><NavigationButton className="tools-detail-back" iconOnly icon={<ArrowLeft />} label={s.back} onClick={() => { setSelected(null); setKey(""); setError(""); }} /><div><h2>{current.name}</h2><p>{s.searchDescription}</p></div><span className={`mcp-status ${current.enabled && current.configured ? "is-connected" : "is-disconnected"}`}><span aria-hidden="true" />{status(current)}</span></div>
      <div className="tools-toggle"><strong id="tool-enabled-label">{s.enabled}</strong><Switch checked={enabled} aria-labelledby="tool-enabled-label" onCheckedChange={(value) => { setEnabled(value); setSaved(false); }} /></div>
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
