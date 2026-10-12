import { isTauri } from "@tauri-apps/api/core";
import { load } from "@tauri-apps/plugin-store";

const PREFERENCES_FILE = "preferences.json";
const GLOBAL_CONTEXT_KEY = "global_context";
const GLOBAL_CONTEXT_STORAGE_KEY = "archhypo-flow-global-context";
const LEGACY_CONTEXT_STORAGE_KEY = "archhypo-flow-global-agent-instructions";

let preferencesStore: ReturnType<typeof load> | undefined;

async function getPreferencesStore() {
  preferencesStore ??= load(PREFERENCES_FILE, { autoSave: false });
  return preferencesStore;
}

export async function getGlobalContext(): Promise<string> {
  if (!isTauri()) {
    const saved = localStorage.getItem(GLOBAL_CONTEXT_STORAGE_KEY);
    if (saved !== null) return saved;

    const legacy = localStorage.getItem(LEGACY_CONTEXT_STORAGE_KEY) ?? "";
    if (legacy) {
      localStorage.setItem(GLOBAL_CONTEXT_STORAGE_KEY, legacy);
      localStorage.removeItem(LEGACY_CONTEXT_STORAGE_KEY);
    }
    return legacy;
  }

  const store = await getPreferencesStore();
  const saved = await store.get<string>(GLOBAL_CONTEXT_KEY);
  if (typeof saved === "string") return saved;

  const legacy =
    localStorage.getItem(LEGACY_CONTEXT_STORAGE_KEY) ??
    localStorage.getItem(GLOBAL_CONTEXT_STORAGE_KEY);
  if (legacy !== null) {
    await store.set(GLOBAL_CONTEXT_KEY, legacy);
    await store.save();
    localStorage.removeItem(LEGACY_CONTEXT_STORAGE_KEY);
    localStorage.removeItem(GLOBAL_CONTEXT_STORAGE_KEY);
    return legacy;
  }

  return "";
}

export async function saveGlobalContext(globalContext: string): Promise<string> {
  if (isTauri()) {
    const store = await getPreferencesStore();
    await store.set(GLOBAL_CONTEXT_KEY, globalContext);
    await store.save();
  } else {
    localStorage.setItem(GLOBAL_CONTEXT_STORAGE_KEY, globalContext);
  }

  localStorage.removeItem(LEGACY_CONTEXT_STORAGE_KEY);
  if (isTauri()) localStorage.removeItem(GLOBAL_CONTEXT_STORAGE_KEY);
  return globalContext;
}
