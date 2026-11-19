import { isTauri } from "@tauri-apps/api/core";
import { openUrl } from "@tauri-apps/plugin-opener";
import { IconCheck as Check, IconChevronDown as ChevronDown, IconAlertCircle as CircleAlert, IconCpu as Cpu, IconEye as Eye, IconEyeOff as EyeOff, IconSearch as Search } from "@tabler/icons-react";
import openaiIcon from "../../../assets/model-providers/openai.svg?raw";
import anthropicIcon from "../../../assets/model-providers/anthropic.svg?raw";
import googleIcon from "../../../assets/model-providers/google.svg?raw";
import metaIcon from "../../../assets/model-providers/meta.svg?raw";
import mistralIcon from "../../../assets/model-providers/mistralai.svg?raw";
import deepseekIcon from "../../../assets/model-providers/deepseek.svg?raw";
import xaiIcon from "../../../assets/model-providers/xai.svg?raw";
import alibabaIcon from "../../../assets/model-providers/alibabacloud.svg?raw";
import cohereIcon from "../../../assets/model-providers/cohere.svg?raw";
import nvidiaIcon from "../../../assets/model-providers/nvidia.svg?raw";
import microsoftIcon from "../../../assets/model-providers/microsoft.svg?raw";
import perplexityIcon from "../../../assets/model-providers/perplexity.svg?raw";
import moonshotIcon from "../../../assets/model-providers/moonshot.svg?raw";
import minimaxIcon from "../../../assets/model-providers/minimax.svg?raw";
import bytedanceIcon from "../../../assets/model-providers/bytedance.svg?raw";
import tencentIcon from "../../../assets/model-providers/tencent.svg?raw";
import zaiIcon from "../../../assets/model-providers/zai.svg?raw";
import basetenIcon from "../../../assets/model-providers/baseten.svg?raw";
import cloudflareIcon from "../../../assets/model-providers/cloudflare.svg?raw";
import liquidIcon from "../../../assets/model-providers/liquid.svg?raw";
import morphIcon from "../../../assets/model-providers/morph.svg?raw";
import upstageIcon from "../../../assets/model-providers/upstage.svg?raw";
import togetherIcon from "../../../assets/model-providers/together.svg?raw";
import typesafeIcon from "../../../assets/model-providers/typesafe.png";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type en from "../../../i18n/locales/en.json";
import "./ProviderSettings.css";

type Config = { configured: boolean; openrouter_model: string; system_one_model: string };
type Model = { id: string; name: string; pricing?: { prompt?: string; completion?: string } };
const API = "http://127.0.0.1:8765/api/providers/openrouter";

const providerIcons: Record<string, string> = {
  openai: openaiIcon, anthropic: anthropicIcon, google: googleIcon,
  "meta-llama": metaIcon, meta: metaIcon, mistralai: mistralIcon,
  deepseek: deepseekIcon, "x-ai": xaiIcon, qwen: alibabaIcon, alibaba: alibabaIcon,
  cohere: cohereIcon, nvidia: nvidiaIcon, microsoft: microsoftIcon, perplexity: perplexityIcon,
  moonshotai: moonshotIcon, minimax: minimaxIcon, bytedance: bytedanceIcon,
  tencent: tencentIcon, "z-ai": zaiIcon,
  baseten: basetenIcon, cloudflare: cloudflareIcon, liquid: liquidIcon,
  morph: morphIcon, upstage: upstageIcon, togethercomputer: togetherIcon,
};

function ModelIcon({ modelId }: { modelId: string }) {
  const provider = modelId.replace(/^openrouter:/i, "").split("/")[0].replace(/^~/, "").toLowerCase();
  const icon = providerIcons[provider];
  // These SVGs are bundled application assets, never data from the model catalog.
  return <span className="provider-model-icon" aria-hidden="true">{provider === "typesafe" ? <img className="provider-model-image" src={typesafeIcon} alt="" /> : icon ? <span className="provider-model-logo" dangerouslySetInnerHTML={{ __html: icon }} /> : <Cpu size={17} />}</span>;
}

function priceText(value: string | undefined, missing: string, format: string, locale: string): string {
  if (value === undefined || !value.trim()) return missing;
  const price = Number(value);
  if (!Number.isFinite(price) || price < 0) return missing;
  return format.replace("{{value}}", (price * 1_000_000).toLocaleString(locale, { maximumFractionDigits: 6 }));
}

function ModelSelector({ id, label, value, models, onChange, hintId }: { id: string; label: string; value: string; models: Model[]; onChange: (value: string) => void; hintId?: string }) {
  const s = useLabels();
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const selected = models.find((model) => model.id === value);
  function priceTooltip(model: Model | undefined) { const price = (value: string | undefined) => priceText(value, s.priceMissing, s.pricePerMillion, i18n.resolvedLanguage ?? "pt-BR"); return `${s.priceInput}: ${price(model?.pricing?.prompt)}\n${s.priceOutput}: ${price(model?.pricing?.completion)}`; }
  const filtered = models.filter((model) => `${model.name} ${model.id}`.toLowerCase().includes(query.trim().toLowerCase()));
  const custom = query.trim() && !models.some((model) => model.id === query.trim()) ? query.trim() : "";
  const options = [...filtered.map((model) => model.id), ...(custom ? [custom] : [])];
  useEffect(() => {
    if (!open) return;
    searchRef.current?.focus();
    function outside(event: PointerEvent) { if (!root.current?.contains(event.target as Node)) setOpen(false); }
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, [open]);
  useEffect(() => {
    if (open) document.getElementById(`${id}-option-${active}`)?.scrollIntoView({ block: "nearest" });
  }, [id, active, open]);
  function choose(modelId: string) {
    onChange(modelId);
    setOpen(false);
    setQuery("");
    root.current?.querySelector<HTMLButtonElement>(".provider-model-trigger")?.focus();
  }
  return <div className="provider-model-selector" ref={root}>
    <button id={id} className="provider-model-trigger" type="button" title={value ? priceTooltip(selected) : undefined} aria-label={label} aria-describedby={hintId} aria-expanded={open} aria-haspopup="listbox" onClick={() => { setOpen(!open); setQuery(""); setActive(0); }}>{value && <ModelIcon modelId={value} />}<span>{selected ? `${selected.name} (${selected.id})` : value || s.select}</span><ChevronDown size={16} aria-hidden="true" /></button>
    {open && <div className="provider-model-menu" onKeyDown={(event) => {
      if (event.key === "Escape") { event.stopPropagation(); setOpen(false); root.current?.querySelector<HTMLButtonElement>(".provider-model-trigger")?.focus(); }
      else if (event.key === "ArrowDown") { event.preventDefault(); setActive((index) => Math.min(index + 1, options.length - 1)); }
      else if (event.key === "ArrowUp") { event.preventDefault(); setActive((index) => Math.max(index - 1, 0)); }
      else if (event.key === "Enter" && options[active]) { event.preventDefault(); choose(options[active]); }
    }}>
      <div className="provider-model-search"><Search size={16} aria-hidden="true" /><input ref={searchRef} role="combobox" aria-label={s.select} aria-expanded="true" aria-controls={`${id}-list`} aria-activedescendant={options[active] ? `${id}-option-${active}` : undefined} placeholder={s.select} value={query} onChange={(event) => { setQuery(event.target.value); setActive(0); }} /></div>
      <div className="provider-model-options" id={`${id}-list`} role="listbox" aria-label={label}>{filtered.map((model, index) => <button id={`${id}-option-${index}`} key={model.id} type="button" role="option" title={priceTooltip(model)} aria-selected={model.id === value} className={`provider-model-option${index === active ? " is-active" : ""}`} onMouseEnter={() => setActive(index)} onClick={() => choose(model.id)}><ModelIcon modelId={model.id} /><span className="provider-model-option-text"><strong>{model.name}</strong><small>{model.id}</small></span>{model.id === value && <Check size={16} aria-hidden="true" />}</button>)}{custom && <button id={`${id}-option-${filtered.length}`} type="button" role="option" aria-selected={false} className={`provider-model-option${active === filtered.length ? " is-active" : ""}`} onMouseEnter={() => setActive(filtered.length)} onClick={() => choose(custom)}><ModelIcon modelId={custom} /><span className="provider-model-option-text"><strong>{s.custom}</strong><small>{custom}</small></span></button>}{options.length === 0 && <p className="provider-model-empty">{s.noModels}</p>}</div>
    </div>}
  </div>;
}

function useLabels() {
  const { t } = useTranslation();
  return t("settingsPages.providers", { returnObjects: true }) as typeof en.settingsPages.providers;
}

export function ModelsSettings() {
  const s = useLabels();
  const [config, setConfig] = useState<Config | null>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [decisionModels, setDecisionModels] = useState<Model[]>([]);
  const [key, setKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [error, setError] = useState("");
  const [catalogError, setCatalogError] = useState(false);
  const [usingCache, setUsingCache] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(API, { signal: controller.signal }).then((response) => { if (!response.ok) throw new Error(); return response.json() as Promise<Config>; }).then(setConfig).catch(() => { if (!controller.signal.aborted) setError(s.loadError); });
    fetch(`${API}/models`, { signal: controller.signal }).then((response) => { if (!response.ok) throw new Error(); if (response.headers.get("X-Model-Cache") === "stale") setUsingCache(true); return response.json() as Promise<Model[]>; }).then(setModels).catch(() => { if (!controller.signal.aborted) setCatalogError(true); });
    fetch(`${API}/models?kind=decisions`, { signal: controller.signal }).then((response) => { if (!response.ok) throw new Error(); if (response.headers.get("X-Model-Cache") === "stale") setUsingCache(true); return response.json() as Promise<Model[]>; }).then(setDecisionModels).catch(() => { if (!controller.signal.aborted) setCatalogError(true); });
    return () => controller.abort();
  }, [s.loadError]);
  async function save() {
    if (!config) return;
    setSaving(true); setError(""); setSaved(false);
    try {
      const response = await fetch(API, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ openrouter_model: config.openrouter_model.trim(), system_one_model: config.system_one_model.trim(), ...(key.trim() ? { api_key: key.trim() } : {}) }) });
      if (!response.ok) { setError(response.status === 503 ? s.keyringError : s.saveError); return; }
      setConfig(await response.json() as Config); setKey(""); setShowKey(false); setSaved(true);
    } catch { setError(s.saveError); }
    finally { setSaving(false); }
  }
  return <section className="settings-page provider-page">
    <p className="settings-page-description">{s.description}</p>
    {!config ? <p role={error ? "alert" : undefined}>{error || s.loading}</p> : <>
      <div className="provider-field"><label htmlFor="openrouter-key">{s.key}</label><div className="provider-key"><input id="openrouter-key" type={showKey ? "text" : "password"} autoComplete="off" spellCheck={false} placeholder={config.configured ? s.existing : s.enter} value={key} onChange={(event) => { setKey(event.target.value); setSaved(false); }} aria-describedby="openrouter-key-hint" /><button type="button" onClick={() => setShowKey(!showKey)} aria-label={showKey ? s.hide : s.show} title={showKey ? s.hide : s.show}>{showKey ? <EyeOff size={17} /> : <Eye size={17} />}</button></div><small id="openrouter-key-hint">{s.env}</small></div>
      <div className="provider-field"><label htmlFor="openrouter-model">{s.chat}</label><div className="provider-model-row"><ModelSelector id="openrouter-model" label={s.chat} value={config.openrouter_model} models={models} onChange={(value) => { setConfig({ ...config, openrouter_model: value }); setSaved(false); }} hintId="default-model-hint" /><a className="model-pricing-trigger" href="https://openrouter.ai/models" target="_blank" rel="noopener noreferrer" aria-label={s.pricingOpen} title={s.pricingOpen} onClick={(event) => { if (!isTauri()) return; event.preventDefault(); void openUrl("https://openrouter.ai/models").catch((error: unknown) => console.error("Could not open OpenRouter model catalog", error)); }}><CircleAlert size={19} aria-hidden="true" /></a></div><small id="default-model-hint">{s.defaultHint}</small></div>
      <div className="provider-field"><label htmlFor="system-one-model">{s.system}</label><ModelSelector id="system-one-model" label={s.system} value={config.system_one_model} models={decisionModels} onChange={(value) => { setConfig({ ...config, system_one_model: value }); setSaved(false); }} hintId="system-model-hint" /><small id="system-model-hint">{s.compatibility}</small></div>
      {catalogError && <p className="provider-warning" role="status">{s.catalogError}</p>}
      {usingCache && <p className="provider-warning" role="status">{s.cacheNotice}</p>}
      <p className="provider-hint">{s.restart}</p>
      <button className="provider-save" type="button" disabled={saving || !config.openrouter_model.trim() || !config.system_one_model.trim()} onClick={() => void save()}>{saving ? s.saving : s.save}</button>
      {saved && <p className="provider-success" role="status">{s.saved}</p>}
      {error && <p className="settings-inline-error" role="alert">{error}</p>}
    </>}
  </section>;
}
