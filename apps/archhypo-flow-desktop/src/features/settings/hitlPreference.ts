const HITL_STORAGE_KEY = "archhypo-flow-hitl-enabled";

export function getHitlEnabled(): boolean {
  try {
    return localStorage.getItem(HITL_STORAGE_KEY) !== "false";
  } catch {
    // Keep approval enabled if the saved preference cannot be read.
    return true;
  }
}

export function saveHitlEnabled(enabled: boolean): void {
  localStorage.setItem(HITL_STORAGE_KEY, String(enabled));
}
