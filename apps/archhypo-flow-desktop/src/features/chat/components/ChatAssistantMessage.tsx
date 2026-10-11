import { MessagePrimitive } from "@assistant-ui/react";
import { ChatMarkdownText } from "./ChatMarkdownText";

export type ChatAssistantMessageProps = {
  assistantName?: string;
  avatarLabel?: string;
};

export function ChatAssistantMessage({
  assistantName = "ArchHypo Flow",
  avatarLabel = "A",
}: ChatAssistantMessageProps) {
  return (
    <MessagePrimitive.Root className="chat-message chat-message-assistant">
      <span className="chat-assistant-avatar" aria-hidden="true">
        {avatarLabel}
      </span>
      <div className="chat-assistant-content">
        <span className="chat-assistant-name">{assistantName}</span>
        <MessagePrimitive.Parts components={{ Text: ChatMarkdownText }} />
      </div>
    </MessagePrimitive.Root>
  );
}
