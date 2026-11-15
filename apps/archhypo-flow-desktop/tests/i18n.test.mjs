import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import ts from "typescript";
import i18next from "i18next";

const root = path.resolve(import.meta.dirname, "..");
const sourceRoot = path.join(root, "src");
const en = JSON.parse(fs.readFileSync(path.join(sourceRoot, "i18n/locales/en.json"), "utf8"));
const pt = JSON.parse(fs.readFileSync(path.join(sourceRoot, "i18n/locales/pt-BR.json"), "utf8"));

function keys(value, prefix = "") {
  if (Array.isArray(value)) return value.flatMap((item, index) => keys(item, `${prefix}.${index}`));
  if (value && typeof value === "object") return Object.entries(value).flatMap(([key, item]) => keys(item, prefix ? `${prefix}.${key}` : key));
  return [prefix];
}

function sourceFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(dir, entry.name);
    return entry.isDirectory() ? sourceFiles(file) : /\.(tsx|ts)$/.test(entry.name) ? [file] : [];
  });
}

test("translation catalogs have the same keys", () => {
  assert.deepEqual(keys(en).sort(), keys(pt).sort());
});

test("settings and review samples follow the selected language", async () => {
  const i18n = i18next.createInstance();
  await i18n.init({ resources: { en: { translation: en }, "pt-BR": { translation: pt } }, lng: "en", interpolation: { escapeValue: false } });
  assert.equal(i18n.t("settings.observability"), "Observability");
  assert.equal(i18n.t("settingsPages.mcps", { returnObjects: true }).transportStdio, "stdio (local process)");
  assert.equal(i18n.t("settingsPages.providers", { returnObjects: true }).pricePerMillion, "US$ {{value}} / 1M tokens");
  await i18n.changeLanguage("pt-BR");
  assert.equal(i18n.t("settings.observability"), "Observabilidade");
  assert.equal(i18n.t("settingsPages.mcps", { returnObjects: true }).transportStdio, "stdio (processo local)");
  assert.match(i18n.t("reviewSamples", { returnObjects: true }).hypothesis.hypothesis.title, /capacidade/);
});

test("interface JSX does not contain untranslated text or labels", () => {
  const errors = [];
  const visibleAttributes = new Set(["aria-label", "aria-description", "title", "placeholder", "alt"]);
  for (const file of sourceFiles(sourceRoot).filter((name) => name.endsWith(".tsx"))) {
    const source = ts.createSourceFile(file, fs.readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const report = (node, value) => {
      const { line } = source.getLineAndCharacterOfPosition(node.getStart(source));
      errors.push(`${path.relative(root, file)}:${line + 1}: ${JSON.stringify(value)}`);
    };
    function visit(node) {
      if (ts.isJsxText(node) && /\p{L}/u.test(node.text)) {
        const parent = node.parent;
        const hidden = ts.isJsxElement(parent) && parent.openingElement.attributes.properties.some((attr) => ts.isJsxAttribute(attr) && attr.name.getText(source) === "aria-hidden" && attr.initializer?.getText(source) === '"true"');
        if (!hidden) report(node, node.text.trim());
      }
      if (ts.isJsxAttribute(node) && visibleAttributes.has(node.name.getText(source)) && node.initializer) {
        const value = ts.isJsxExpression(node.initializer) ? node.initializer.expression : node.initializer;
        if (value && (ts.isStringLiteral(value) || ts.isNoSubstitutionTemplateLiteral(value)) && value.text) report(node, value.text);
      }
      if (ts.isJsxExpression(node) && node.expression && (ts.isStringLiteral(node.expression) || ts.isNoSubstitutionTemplateLiteral(node.expression)) && /\p{L}/u.test(node.expression.text)) report(node, node.expression.text);
      if (ts.isPropertyAssignment(node) && ["label", "title", "description", "placeholder"].includes(node.name.getText(source)) && ts.isStringLiteral(node.initializer) && /\p{L}/u.test(node.initializer.text)) report(node, node.initializer.text);
      ts.forEachChild(node, visit);
    }
    visit(source);
  }
  assert.deepEqual(errors, []);
});

test("literal translation keys exist in both catalogs", () => {
  const errors = [];
  const hasKey = (catalog, key) => {
    const get = (name) => name.split(".").reduce((value, part) => value?.[part], catalog);
    return get(key) !== undefined || (get(`${key}_one`) !== undefined && get(`${key}_other`) !== undefined);
  };
  for (const file of sourceFiles(sourceRoot)) {
    const source = ts.createSourceFile(file, fs.readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true, file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    function visit(node) {
      if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === "t" && node.arguments.length && ts.isStringLiteral(node.arguments[0])) {
        const key = node.arguments[0].text;
        if (!hasKey(en, key) || !hasKey(pt, key)) errors.push(`${path.relative(root, file)}: ${key}`);
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
  }
  assert.deepEqual(errors, []);
});
