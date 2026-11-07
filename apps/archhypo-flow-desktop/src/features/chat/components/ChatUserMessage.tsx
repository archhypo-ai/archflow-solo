import { MessagePrimitive, useAuiState } from "@assistant-ui/react";
import { ChatMarkdownText } from "./ChatMarkdownText";
import { ChatMessageActions } from "./ChatMessageActions";
import { MessageAttachments } from "./MessageAttachments";
import { attachmentFolder } from "../adapters/documentAttachmentAdapter";
import { groupMessageAttachments } from "../adapters/groupMessageAttachments";

export function ChatUserMessage() {
  const isReviewAction = useAuiState(
    ({ message }) => message.metadata.custom.isReviewAction,
  );
  const attachments = useAuiState(({ message }) => message.attachments);
  const storedSizes = useAuiState(({ message }) => message.metadata.custom.attachmentSizes);
  const storedFolders = useAuiState(({ message }) => message.metadata.custom.attachmentFolders);
  const hasText = useAuiState(({ message }) =>
    message.content.some((part) => part.type === "text" && part.text.trim().length > 0),
  );
  if (isReviewAction) return null;

  return (
    <MessagePrimitive.Root className="chat-message chat-message-user">
      <MessageAttachments attachments={groupMessageAttachments((attachments ?? []).map((attachment, index) => {
        const storedSize = Array.isArray(storedSizes) ? storedSizes[index] : undefined;
        const storedFolder = Array.isArray(storedFolders) ? storedFolders[index] : undefined;
        const folder = attachmentFolder(attachment.file) ?? (
          storedFolder && typeof storedFolder === "object" &&
          typeof storedFolder.id === "string" && typeof storedFolder.name === "string"
            ? { id: storedFolder.id, name: storedFolder.name }
            : undefined
        );
        return {
          id: attachment.id,
          name: attachment.name,
          sizeBytes: attachment.file?.size ?? (typeof storedSize === "number" ? storedSize : undefined),
          folder,
        };
      }))} />
      {hasText && <div className="chat-message-bubble">
        <MessagePrimitive.Parts components={{ Text: ChatMarkdownText }} />
      </div>}
      <ChatMessageActions />
    </MessagePrimitive.Root>
  );
}
