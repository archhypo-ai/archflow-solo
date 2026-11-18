import { IconBook as BookOpen, IconChevronRight as ChevronRight, IconCode as Code2, IconEye as Eye, IconFilePlus as FilePlus2, IconFolderOpen as FolderOpen, IconPlus as Plus, IconSearch as Search, IconTrash as Trash2, IconX as X } from "@tabler/icons-react";
import { isTauri } from "@tauri-apps/api/core";
import { openPath } from "@tauri-apps/plugin-opener";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import ReactMarkdown from "react-markdown";
import { useTranslation } from "react-i18next";
import type en from "../../../i18n/locales/en.json";
import remarkGfm from "remark-gfm";
import "./SkillsSettings.css";

type Skill = { name: string; description: string; error: string };
type SkillDetail = Skill & { files: Record<string, string>; revision: string; unavailable: string[] };
const API = "http://127.0.0.1:8765/api/skills";

export function SkillsSettings() {
  const { t } = useTranslation();
  const s = t("settingsPages.skills", { returnObjects: true }) as typeof en.settingsPages.skills;
  const [skills, setSkills] = useState<Skill[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [folderError, setFolderError] = useState("");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<SkillDetail | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<Record<string, string>>({ "SKILL.md": "" });
  const [activeFile, setActiveFile] = useState("SKILL.md");
  const [newFile, setNewFile] = useState<string | null>(null);
  const [preview, setPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draftError, setDraftError] = useState("");
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const pageRef = useRef<HTMLDivElement>(null);

  async function loadSkills() {
    setError("");
    try {
      const response = await fetch(API);
      if (!response.ok) throw new Error();
      setSkills(await response.json() as Skill[]);
    } catch { setSkills([]); setError(s.error); }
  }
  useEffect(() => { void loadSkills(); }, []);
  useEffect(() => {
    if (!creating) return;
    const container = pageRef.current?.closest<HTMLElement>(".settings-content");
    if (!container) return;
    const previousOverflow = container.style.overflowY;
    container.style.overflowY = "hidden";
    return () => { container.style.overflowY = previousOverflow; };
  }, [creating]);
  useEffect(() => {
    if (!creating) return;
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      if (!saving) setCreating(false);
    };
    document.addEventListener("keydown", handleEscape, true);
    return () => document.removeEventListener("keydown", handleEscape, true);
  }, [creating, saving]);
  async function openFolder() {
    setFolderError("");
    if (!isTauri()) { setFolderError(s.folderDesktopOnly); return; }
    try {
      const response = await fetch(`${API}/folder`, { method: "POST" });
      if (!response.ok) throw new Error();
      const { path } = await response.json() as { path: string };
      await openPath(path);
    } catch { setFolderError(s.folderError); }
  }
  function startCreate() {
    setEditing(null); setName(""); setDescription(""); setFiles({ "SKILL.md": "" }); setActiveFile("SKILL.md");
    setNewFile(null); setPreview(false); setDraftError(""); setCreating(true);
  }
  async function openSkill(skill: Skill) {
    setError("");
    try {
      const response = await fetch(`${API}/${encodeURIComponent(skill.name)}`);
      if (!response.ok) { const data = await response.json() as { detail?: string }; throw new Error(data.detail || s.error); }
      const detail = await response.json() as SkillDetail;
      setEditing(detail); setName(detail.name); setDescription(detail.description); setFiles(detail.files);
      setActiveFile("SKILL.md"); setNewFile(null); setPreview(false); setDraftError(""); setCreating(true);
    } catch (err) { setError(err instanceof Error ? err.message : s.error); }
  }
  async function deleteSkill() {
    if (!editing || !window.confirm(s.confirmDelete.replace("{name}", editing.name))) return;
    setSaving(true); setDraftError("");
    try {
      const response = await fetch(`${API}/${encodeURIComponent(editing.name)}`, { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ revision: editing.revision }) });
      if (!response.ok) { const data = await response.json() as { detail?: string }; throw new Error(data.detail || s.error); }
      setCreating(false); await loadSkills();
    } catch (err) { setDraftError(err instanceof Error ? err.message : s.error); }
    finally { setSaving(false); }
  }
  function addFile() {
    const value = newFile?.trim() ?? "";
    if (!value || value.startsWith("/") || value.includes("\\") || value.split("/").some((part) => !part || part.startsWith(".")) || value.toLowerCase() === "skill.md" || value in files) { setDraftError(s.pathInvalid); return; }
    setFiles({ ...files, [value]: "" }); setActiveFile(value); setNewFile(null); setDraftError("");
  }
  async function createSkill() {
    if (!name.trim() || !description.trim() || !files["SKILL.md"].trim()) { setDraftError(s.required); return; }
    setSaving(true); setDraftError("");
    try {
      const { "SKILL.md": instructions, ...references } = files;
      const response = await fetch(editing ? `${API}/${encodeURIComponent(editing.name)}` : API, { method: editing ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: name.trim(), description: description.trim(), instructions, files: references, ...(editing ? { revision: editing.revision } : {}) }) });
      if (!response.ok) {
        if (response.status === 409) throw new Error(editing ? s.conflict : s.exists);
        const body = await response.json() as { detail?: unknown };
        throw new Error(typeof body.detail === "string" ? body.detail : s.required);
      }
      setCreating(false); await loadSkills();
    } catch (err) { setDraftError(err instanceof Error ? err.message : s.error); }
    finally { setSaving(false); }
  }
  const visible = skills.filter((skill) => `${skill.name} ${skill.description}`.toLowerCase().includes(search.toLowerCase()));
  return <div ref={pageRef} className="skills-page">
    <p className="settings-page-description">{s.subtitle}</p>
    <div className="skills-toolbar"><div className="skills-search"><Search size={16} /><input aria-label={s.search} placeholder={s.search} value={search} onChange={(e) => setSearch(e.target.value)} /></div>
      <div className="skills-toolbar-actions"><button className="skills-folder-button" type="button" onClick={() => void openFolder()}><FolderOpen size={16} /> {s.folder}</button>
      <button className="skills-primary" type="button" onClick={startCreate}><Plus size={16} /> {s.add}</button></div></div>
    {folderError && <p className="skills-error" role="alert">{folderError}</p>}
    {error && <p className="skills-error" role="alert">{error}</p>}
    {!error && visible.length === 0 ? <p className="skills-empty">{s.empty}</p> : <div className="skills-list">{visible.map((skill) => <button type="button" className="skills-item" key={skill.name} onClick={() => void openSkill(skill)}><span className="skills-item-icon"><BookOpen size={18} /></span><span className="skills-item-content"><strong>{skill.name}</strong><span>{skill.error ? `${s.invalid}: ${skill.error}` : skill.description}</span></span><ChevronRight className="skills-item-chevron" size={16} aria-hidden="true" /></button>)}</div>}
    {creating && createPortal(<div className="skill-editor-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget && !saving) setCreating(false); }}><section className="skill-editor" role="dialog" aria-modal="true" aria-labelledby="skill-editor-title" onKeyDown={(e) => { if (e.key === "Escape") { e.stopPropagation(); if (!saving) setCreating(false); } }}>
      <header><strong id="skill-editor-title">{editing ? s.editSkill : s.create}</strong><button type="button" aria-label={s.cancel} onClick={() => setCreating(false)}><X size={18} /></button></header>
      <label>{s.name}<input autoFocus disabled={!!editing} value={name} onChange={(e) => setName(e.target.value)} placeholder={s.nameExample} maxLength={64} /></label><small>{s.nameHint}{name && ` · /${name}`}</small>
      <label>{s.description}<textarea className="skill-description" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={1024} /></label>
      {editing?.error && <p className="skills-error" role="status">{s.invalid}: {editing.error}</p>}
      {editing && editing.unavailable.length > 0 && <details className="skill-unavailable"><summary>{editing.unavailable.includes("SKILL.md") ? s.skillUnavailable : `${s.unavailable} (${editing.unavailable.length})`}</summary><ul>{editing.unavailable.map((file) => <li key={file}>{file}</li>)}</ul></details>}
      <div className="skill-workspace"><aside><div className="skill-file-list">{Object.keys(files).map((file) => <button type="button" key={file} className={activeFile === file ? "is-active" : ""} onClick={() => { setActiveFile(file); setPreview(false); }}>{file}</button>)}
        {newFile !== null && <input autoFocus value={newFile} placeholder={s.filePath} onChange={(e) => setNewFile(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addFile(); } }} />}</div><button type="button" className="skill-add-file" onClick={() => newFile === null ? setNewFile("") : addFile()}><FilePlus2 size={15} /> {s.addFile}</button></aside>
        <div className="skill-file-editor"><div className="skill-file-header"><span>/{activeFile}</span><div><button type="button" title={s.preview} aria-label={s.preview} aria-pressed={preview} onClick={() => setPreview(true)}><Eye size={16} /></button><button type="button" title={s.edit} aria-label={s.edit} aria-pressed={!preview} onClick={() => setPreview(false)}><Code2 size={16} /></button>{activeFile !== "SKILL.md" && <button type="button" title={s.remove} aria-label={s.remove} onClick={() => { const next = { ...files }; delete next[activeFile]; setFiles(next); setActiveFile("SKILL.md"); }}><Trash2 size={16} /></button>}</div></div>
        {preview ? <div className="skill-preview">{/\.(md|markdown|mdx)$/i.test(activeFile) ? <div className="skill-markdown"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{ a: ({ children }) => <span>{children}</span>, img: ({ alt }) => <span>{alt ?? ""}</span> }}>{files[activeFile]}</ReactMarkdown></div> : <pre><code>{files[activeFile]}</code></pre>}</div> : <div className="skill-code-editor">
          <div ref={lineNumbersRef} className="skill-line-numbers" aria-hidden="true">{files[activeFile].split("\n").map((_, index) => <span key={index}>{index + 1}</span>)}</div>
          <textarea aria-label={activeFile} spellCheck={false} wrap="off" placeholder={activeFile === "SKILL.md" ? s.instructions : ""} value={files[activeFile]} onScroll={(e) => { if (lineNumbersRef.current) lineNumbersRef.current.scrollTop = e.currentTarget.scrollTop; }} onChange={(e) => setFiles({ ...files, [activeFile]: e.target.value })} />
        </div>}</div></div>
      {draftError && <p className="skills-error" role="alert">{draftError}</p>}
      <footer>{editing ? <button className="skill-delete" type="button" onClick={() => void deleteSkill()} disabled={saving}><Trash2 size={16} />{s.deleteSkill}</button> : <span>{s.draft}</span>}<div><button type="button" onClick={() => setCreating(false)} disabled={saving}>{s.cancel}</button><button className="skills-primary" type="button" onClick={() => void createSkill()} disabled={saving || !!editing?.unavailable.includes("SKILL.md")}>{saving ? s.saving : editing ? s.saveChanges : s.save}</button></div></footer>
    </section></div>, document.body)}
  </div>;
}
