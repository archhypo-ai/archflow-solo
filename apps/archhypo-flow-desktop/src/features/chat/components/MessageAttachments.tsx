import { FileText, FolderOpen } from "lucide-react";

export type MessageAttachmentItem = {
  id: string;
  name: string;
  sizeBytes?: number;
  kind?: "file" | "folder";
};

/** Static received-files layout, following assistant-ui's MessageAttachments. */
export function MessageAttachments({ attachments }: { attachments: MessageAttachmentItem[] }) {
  if (attachments.length === 0) return null;
  return (
    <div className="chat-message-attachments">
      {attachments.map((attachment) => (
        <div className="chat-message-attachment" key={attachment.id}>
          <span className="chat-attachment-icon">
            {attachment.kind === "folder" ? <FolderOpen size={18} aria-hidden="true" /> : <FileText size={18} aria-hidden="true" />}
          </span>
          <span className="chat-message-attachment-details">
            <span className="chat-attachment-name" title={attachment.name}>{attachment.name}</span>
            {attachment.sizeBytes !== undefined && (
              <span className="chat-message-attachment-size">{formatFileSize(attachment.sizeBytes)}</span>
            )}
          </span>
        </div>
      ))}
    </div>
  );
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
