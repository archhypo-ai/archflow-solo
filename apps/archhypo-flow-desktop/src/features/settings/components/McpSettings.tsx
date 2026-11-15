import { isTauri } from "@tauri-apps/api/core";
import { openPath } from "@tauri-apps/plugin-opener";
import { ArrowLeft, Cable, FileJson, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";
import { SelectMenu } from "../../../components/overlay";
import "./SkillsSettings.css";
import "./McpSettings.css";

type Transport = "stdio" | "sse" | "streamable-http";
type Tool = { name: string; description: string; inputSchema: unknown };
type Server = { id: string; transport: Transport; auto_connect: boolean; command: string; args: string[]; env: Record<string, string>; cwd: string; url: string; status: "disconnected" | "connecting" | "connected" | "error"; tools: Tool[]; error: string | null };
type Form = { id: string; transport: Transport; auto_connect: boolean; command: string; args: string; env: string; cwd: string; url: string };
const API = "http://127.0.0.1:8765/api/mcps";
const emptyForm = (): Form => ({ id: "", transport: "stdio", auto_connect: false, command: "", args: "", env: "", cwd: "", url: "" });
const words = {
  pt: { description: "Gerencie e conecte servidores MCP para descobrir suas ferramentas.", search: "Buscar MCPs", fileEdit: "Editar", add: "Adicionar", empty: "Nenhum MCP encontrado.", create: "Adicionar servidor", edit: "Editar servidor", id: "ID do servidor", idHelp: "Usado como chave no mcp.json. Letras, números, hífens e underscores.", transport: "Transporte", command: "Comando", args: "Argumentos", argsHelp: "Um argumento por linha.", env: "Ambiente", envHelp: "Uma variável KEY=VALUE por linha. Use ${NOME} para valores do ambiente; textos digitados são salvos no mcp.json.", cwd: "Diretório de trabalho", inherited: "(herdado)", url: "URL", cancel: "Cancelar", save: "Salvar", connect: "Conectar", disconnect: "Desconectar", connecting: "Conectando", connected: "Conectado", disconnected: "Desconectado", error: "Erro", tools: "Ferramentas", none: "Nenhuma ferramenta encontrada.", notDiscovered: "Conecte para descobrir as ferramentas.", back: "Voltar para MCPs", config: "Configuração", delete: "Remover", confirmDelete: "Remover este servidor? A conexão será encerrada.", details: "Detalhes", schema: "Esquema de entrada", failure: "Não foi possível acessar o gerenciador MCP.", invalidEnv: "Cada linha de ambiente deve conter KEY=VALUE.", fileDesktop: "Abrir o arquivo está disponível apenas no aplicativo desktop.", fileError: "Não foi possível abrir o arquivo mcp.json.", executeNotice: "Conectar iniciará o comando local configurado.", loading: "Carregando...", refresh: "Atualizar", editDisconnect: "Salvar alterações desconectará o servidor.", mcpFile: "Configuração: ~/.archhypoflow/mcp.json" },
  en: { description: "Manage and connect MCP servers to discover their tools.", search: "Search MCPs", fileEdit: "Edit", add: "Add", empty: "No MCPs found.", create: "Add server", edit: "Edit server", id: "Server ID", idHelp: "Used as the mcp.json key. Letters, numbers, hyphens and underscores.", transport: "Transport", command: "Command", args: "Arguments", argsHelp: "One argument per line.", env: "Environment", envHelp: "One KEY=VALUE per line. Use ${NAME} for environment values; literal values are saved in mcp.json.", cwd: "Working directory", inherited: "(inherited)", url: "URL", cancel: "Cancel", save: "Save", connect: "Connect", disconnect: "Disconnect", connecting: "Connecting", connected: "Connected", disconnected: "Disconnected", error: "Error", tools: "Tools", none: "No tools found.", notDiscovered: "Connect to discover tools.", back: "Back to MCPs", config: "Configuration", delete: "Remove", confirmDelete: "Remove this server? Its connection will be closed.", details: "Details", schema: "Input schema", failure: "Could not access the MCP manager.", invalidEnv: "Each environment line must contain KEY=VALUE.", fileDesktop: "Opening the file is only available in the desktop app.", fileError: "Could not open mcp.json.", executeNotice: "Connecting will start the configured local command.", loading: "Loading...", refresh: "Refresh", editDisconnect: "Saving changes will disconnect the server.", mcpFile: "Configuration: ~/.archhypoflow/mcp.json" },
};

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, headers: { ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers } });
  if (!response.ok) {
    const data = await response.json().catch(() => ({})) as { detail?: unknown };
    throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return await response.json() as T;
}

export function McpSettings() {
  const { i18n } = useTranslation();
  const s = i18n.resolvedLanguage?.startsWith("pt") ? words.pt : words.en;
  const [servers, setServers] = useState<Server[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [form, setForm] = useState<Form | null>(null);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    try { setServers(await request<Server[]>(API)); setError(""); }
    catch (err) { setError(err instanceof Error ? err.message : s.failure); }
    finally { setLoading(false); }
  }, [s.failure]);
  useEffect(() => { void load(); const timer = window.setInterval(() => void load(), 2500); return () => window.clearInterval(timer); }, [load]);
  useEffect(() => {
    if (!form) return;
    const key = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      const openSelect = document.querySelector<HTMLButtonElement>(".mcp-modal .settings-select-menu.is-open .settings-select-trigger");
      if (openSelect) { openSelect.click(); return; }
      if (!busy) setForm(null);
    };
    document.addEventListener("keydown", key, true);
    return () => document.removeEventListener("keydown", key, true);
  }, [form, busy]);
  const current = servers.find((item) => item.id === selected);
  const filtered = servers.filter((item) => `${item.id} ${item.transport}`.toLowerCase().includes(search.toLowerCase()));
  function edit(server: Server) {
    setEditing(true); setFormError(""); setForm({ id: server.id, transport: server.transport, auto_connect: server.auto_connect, command: server.command, args: server.args.join("\n"), env: Object.entries(server.env).map(([key, value]) => `${key}=${value}`).join("\n"), cwd: server.cwd, url: server.url });
  }
  async function save() {
    if (!form) return;
    const env: Record<string, string> = {};
    for (const line of form.env.split("\n")) {
      if (!line.trim()) continue;
      const index = line.indexOf("=");
      if (index < 1 || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(line.slice(0, index).trim())) { setFormError(s.invalidEnv); return; }
      env[line.slice(0, index).trim()] = line.slice(index + 1);
    }
    setBusy(true); setFormError("");
    try {
      const body = { id: form.id.trim(), transport: form.transport, auto_connect: form.auto_connect, command: form.transport === "stdio" ? form.command.trim() : "", args: form.transport === "stdio" ? form.args.split("\n").map((arg) => arg.trim()).filter(Boolean) : [], env: form.transport === "stdio" ? env : {}, cwd: form.transport === "stdio" ? form.cwd.trim() : "", url: form.transport !== "stdio" ? form.url.trim() : "" };
      await request(editing ? `${API}/${encodeURIComponent(form.id)}` : API, { method: editing ? "PUT" : "POST", body: JSON.stringify(body) });
      setForm(null); await load();
    } catch (err) { setFormError(err instanceof Error ? err.message : s.failure); }
    finally { setBusy(false); }
  }
  async function action(server: Server, actionName: "connect" | "disconnect") {
    setError("");
    try { await request(`${API}/${encodeURIComponent(server.id)}/${actionName}`, { method: "POST" }); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : s.failure); }
  }
  async function remove(server: Server) {
    if (!window.confirm(s.confirmDelete)) return;
    try { await request(`${API}/${encodeURIComponent(server.id)}`, { method: "DELETE" }); setSelected(null); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : s.failure); }
  }
  async function editConfigFile() {
    if (!isTauri()) { setError(s.fileDesktop); return; }
    try { const data = await request<{ path: string }>(`${API}/file`, { method: "POST" }); await openPath(data.path); }
    catch { setError(s.fileError); }
  }
  function status(server: Server) { return server.status === "connected" ? s.connected : server.status === "connecting" ? s.connecting : server.status === "error" ? s.error : s.disconnected; }
  function connectButton(server: Server) {
    const active = server.status === "connected" || server.status === "connecting";
    return <button className="mcp-button" type="button" onClick={(event) => { event.stopPropagation(); void action(server, active ? "disconnect" : "connect"); }}>{active ? s.disconnect : s.connect}</button>;
  }
  return <div className="skills-page mcp-page">
    {current ? <>
      <div className="mcp-detail-header"><button className="mcp-back" type="button" onClick={() => setSelected(null)} aria-label={s.back} title={s.back}><ArrowLeft size={18} aria-hidden="true" /></button><div><h2>{current.id}</h2><p>{current.transport}</p></div><span className={`mcp-status is-${current.status}`}><span />{status(current)}</span></div>
      <div className="mcp-detail-actions">{connectButton(current)} <button className="mcp-button" type="button" onClick={() => edit(current)}><Pencil size={14} /> {s.edit}</button><button className="mcp-button mcp-delete" type="button" onClick={() => void remove(current)}><Trash2 size={14} /> {s.delete}</button></div>
      {current.status === "disconnected" && current.transport === "stdio" && <p className="mcp-hint">{s.executeNotice}</p>}
      {current.error && <p className="skills-error" role="alert">{current.error}</p>}
      <h3>{s.tools}{current.status === "connected" ? ` (${current.tools.length})` : ""}</h3>
      {current.status !== "connected" ? <p className="mcp-hint">{s.notDiscovered}</p> : current.tools.length === 0 ? <p className="mcp-hint">{s.none}</p> : <div className="mcp-tools">{current.tools.map((tool) => <details className="mcp-tool" key={tool.name}><summary><strong>{tool.name}</strong><span>{tool.description}</span></summary><div><small>{s.schema}</small><pre>{JSON.stringify(tool.inputSchema, null, 2)}</pre></div></details>)}</div>}
      <h3>{s.config}</h3><div className="mcp-config"><FileJson size={15} /><code>{current.transport === "stdio" ? [current.command, ...current.args].join(" ") : current.url}</code></div>
    </> : <>
      <p className="settings-page-description">{s.description}</p>
      <div className="skills-toolbar"><div className="skills-search"><Search size={16} aria-hidden="true" /><input aria-label={s.search} placeholder={s.search} value={search} onChange={(event) => setSearch(event.target.value)} /></div><div className="skills-toolbar-actions"><button className="skills-folder-button" type="button" onClick={() => void editConfigFile()}><Pencil size={16} />{s.fileEdit}</button><button className="skills-primary" type="button" onClick={() => { setEditing(false); setFormError(""); setForm(emptyForm()); }}><Plus size={16} />{s.add}</button></div></div>
      {loading ? <p className="skills-empty">{s.loading}</p> : !error && !filtered.length ? <p className="skills-empty">{s.empty}</p> : <div className="mcp-server-list">{filtered.map((server) => <button type="button" className="mcp-server-card" key={server.id} onClick={() => setSelected(server.id)}><span className="mcp-server-main"><span className="skills-item-icon"><Cable size={18} /></span><span><strong>{server.id}</strong><small>{server.transport}{server.status === "connected" ? ` · ${server.tools.length} ${s.tools.toLowerCase()}` : ""}</small></span></span><span className={`mcp-status is-${server.status}`}><span />{status(server)}</span></button>)}</div>}
    </>}
    {error && <p className="skills-error" role="alert">{error}</p>}
    {form && createPortal(<div className="mcp-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) setForm(null); }}><section className="mcp-modal" role="dialog" aria-modal="true" aria-labelledby="mcp-form-title"><header><strong id="mcp-form-title">{editing ? s.edit : s.create}</strong><button type="button" aria-label={s.cancel} onClick={() => setForm(null)}><X size={18} /></button></header><div className="mcp-form">
      <label>{s.id} *<small>{s.idHelp}</small><input autoFocus disabled={editing} required pattern="[A-Za-z0-9_-]+" maxLength={100} value={form.id} placeholder="my-server" onChange={(event) => setForm({ ...form, id: event.target.value })} /></label>
      <div className="mcp-transport-field"><span>{s.transport}</span><SelectMenu<Transport> value={form.transport} label={s.transport} options={[{ value: "stdio", label: "stdio (local process)" }, { value: "sse", label: "sse (Server-Sent Events)" }, { value: "streamable-http", label: "streamable-http" }]} onChange={(transport) => setForm({ ...form, transport })} /></div>
      {form.transport === "stdio" ? <><label>{s.command} *<input value={form.command} placeholder="npx" onChange={(event) => setForm({ ...form, command: event.target.value })} /></label><label>{s.args}<small>{s.argsHelp}</small><textarea value={form.args} placeholder={'-y\n@modelcontextprotocol/server-everything'} onChange={(event) => setForm({ ...form, args: event.target.value })} /></label><label>{s.env}<small>{s.envHelp}</small><textarea value={form.env} placeholder="DEBUG=1" onChange={(event) => setForm({ ...form, env: event.target.value })} /></label><label>{s.cwd}<input value={form.cwd} placeholder={s.inherited} onChange={(event) => setForm({ ...form, cwd: event.target.value })} /></label></> : <label>{s.url} *<input type="url" value={form.url} placeholder="https://example.com/mcp" onChange={(event) => setForm({ ...form, url: event.target.value })} /></label>}
      {editing && <p className="mcp-hint">{s.editDisconnect}</p>}{formError && <p className="skills-error" role="alert">{formError}</p>}</div><footer><span>{s.mcpFile}</span><div><button className="mcp-button" type="button" onClick={() => setForm(null)} disabled={busy}>{s.cancel}</button><button className="mcp-submit" type="button" onClick={() => void save()} disabled={busy || !form.id.trim() || (form.transport === "stdio" ? !form.command.trim() : !form.url.trim())}>{editing ? s.save : s.add}</button></div></footer></section></div>, document.body)}
  </div>;
}
