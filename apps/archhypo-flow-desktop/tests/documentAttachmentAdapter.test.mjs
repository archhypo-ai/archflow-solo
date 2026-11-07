import assert from "node:assert/strict";
import { test } from "node:test";
import {
  attachmentFolder,
  invalidExtensions,
  MAX_DOCUMENT_SIZE,
  markFolderAttachments,
  partitionDocuments,
} from "../src/features/chat/adapters/documentAttachmentAdapter.ts";
import { groupMessageAttachments } from "../src/features/chat/adapters/groupMessageAttachments.ts";

test("folder selections group their files without grouping separate selections", () => {
  const first = { name: "one.md", webkitRelativePath: "docs/one.md" };
  const second = { name: "two.md", webkitRelativePath: "docs/two.md" };
  const another = { name: "one.md", webkitRelativePath: "docs/one.md" };
  const standalone = { name: "one.md" };

  markFolderAttachments([first, second]);
  markFolderAttachments([another]);

  assert.equal(attachmentFolder(first).name, "docs");
  assert.equal(attachmentFolder(first).id, attachmentFolder(second).id);
  assert.notEqual(attachmentFolder(first).id, attachmentFolder(another).id);
  assert.equal(attachmentFolder(standalone), undefined);
});

test("mixed selections keep supported files and report invalid extensions", () => {
  const files = [
    { name: "adr.MD", size: 100 },
    { name: "notes.txt", size: 100 },
    { name: "decision.docx", size: 100 },
    { name: "legacy.doc", size: 100 },
    { name: "code.py", size: 10 },
    { name: "other.PY", size: 10 },
    { name: "README", size: 10 },
    { name: "huge.md", size: MAX_DOCUMENT_SIZE + 1 },
  ];
  const result = partitionDocuments(files);
  assert.deepEqual(result.valid.map((file) => file.name), ["adr.MD", "notes.txt", "decision.docx"]);
  assert.deepEqual(invalidExtensions(result.invalid), ["", ".doc", ".py"]);
  assert.deepEqual(result.oversized.map((file) => file.name), ["huge.md"]);
});

test("sent folder is represented by one item without displaying its contents", () => {
  const items = groupMessageAttachments([
    { id: "a", name: "one.md", sizeBytes: 1024, folder: { id: "f", name: "adrs" } },
    { id: "b", name: "two.md", sizeBytes: 2048, folder: { id: "f", name: "adrs" } },
    { id: "c", name: "readme.md", sizeBytes: 100 },
  ]);
  assert.deepEqual(items, [
    { id: "folder-f", name: "adrs", sizeBytes: 3072, kind: "folder" },
    { id: "c", name: "readme.md", sizeBytes: 100, kind: "file" },
  ]);
});
