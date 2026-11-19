export type AttachmentFolder = { id: string; name: string };
const folders = new WeakMap<File, AttachmentFolder>();
export const MAX_DOCUMENT_SIZE = 5 * 1024 * 1024;

export function partitionDocuments<T extends { name: string; size: number }>(files: T[]) {
  const valid: T[] = [];
  const invalid: T[] = [];
  const oversized: T[] = [];
  for (const file of files) {
    if (!/\.(md|txt|docx)$/i.test(file.name)) invalid.push(file);
    else if (file.size > MAX_DOCUMENT_SIZE) oversized.push(file);
    else valid.push(file);
  }
  return { valid, invalid, oversized };
}

export function invalidExtensions(files: Array<{ name: string }>): string[] {
  return [...new Set(files.map(({ name }) => {
    const extension = /\.[^.]+$/.exec(name)?.[0];
    return extension?.toLowerCase() ?? "";
  }))].sort();
}

export function markFolderAttachments(files: File[]): void {
  const group = {
    id: crypto.randomUUID(),
    name: files[0]?.webkitRelativePath.split("/")[0] || "Folder",
  };
  for (const file of files) folders.set(file, group);
}

export function attachmentFolder(file: File | undefined): AttachmentFolder | undefined {
  return file ? folders.get(file) : undefined;
}
