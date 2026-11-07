export type DisplayAttachment = {
  id: string;
  name: string;
  sizeBytes?: number;
  folder?: { id: string; name: string };
};

export function groupMessageAttachments(attachments: DisplayAttachment[]) {
  const result: Array<DisplayAttachment & { kind: "file" | "folder" }> = [];
  const groups = new Map<string, number>();
  for (const attachment of attachments) {
    if (!attachment.folder) {
      result.push({ ...attachment, kind: "file" });
      continue;
    }
    const folder = attachment.folder;
    const index = groups.get(folder.id);
    if (index === undefined) {
      groups.set(folder.id, result.length);
      result.push({
        id: `folder-${folder.id}`,
        name: folder.name,
        sizeBytes: attachment.sizeBytes,
        kind: "folder",
      });
    } else {
      const group = result[index]!;
      group.sizeBytes = group.sizeBytes === undefined || attachment.sizeBytes === undefined
        ? undefined
        : group.sizeBytes + attachment.sizeBytes;
    }
  }
  return result;
}
