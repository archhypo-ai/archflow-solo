import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";
import {
  getHitlEnabled,
  saveHitlEnabled,
} from "../src/features/settings/hitlPreference.ts";

const originalStorage = Object.getOwnPropertyDescriptor(globalThis, "localStorage");
let values;

beforeEach(() => {
  values = new Map();
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, String(value)),
    },
  });
});

afterEach(() => {
  if (originalStorage) {
    Object.defineProperty(globalThis, "localStorage", originalStorage);
  } else {
    delete globalThis.localStorage;
  }
});

test("approval is enabled on first launch", () => {
  assert.equal(getHitlEnabled(), true);
  assert.equal(values.size, 0);
});

test("disabling approval is persisted across module reloads", async () => {
  saveHitlEnabled(false);
  assert.equal(values.get("archhypo-flow-hitl-enabled"), "false");
  const reloaded = await import("../src/features/settings/hitlPreference.ts?reload");
  assert.equal(reloaded.getHitlEnabled(), false);
});

test("approval can be enabled again without changing other preferences", () => {
  values.set("archhypo-flow-theme", "night");
  saveHitlEnabled(false);
  saveHitlEnabled(true);
  assert.equal(getHitlEnabled(), true);
  assert.equal(values.get("archhypo-flow-hitl-enabled"), "true");
  assert.equal(values.get("archhypo-flow-theme"), "night");
});

test("invalid stored values do not silently disable approval", () => {
  for (const value of ["", "invalid", "null", "0"]) {
    values.set("archhypo-flow-hitl-enabled", value);
    assert.equal(getHitlEnabled(), true);
  }
});

test("approval stays enabled when storage cannot be read", () => {
  globalThis.localStorage.getItem = () => {
    throw new Error("Storage is unavailable");
  };
  assert.equal(getHitlEnabled(), true);
});

test("storage write failures can be reported by the settings UI", () => {
  globalThis.localStorage.setItem = () => {
    throw new Error("Storage is unavailable");
  };
  assert.throws(() => saveHitlEnabled(false), /Storage is unavailable/);
  assert.equal(getHitlEnabled(), true);
});
