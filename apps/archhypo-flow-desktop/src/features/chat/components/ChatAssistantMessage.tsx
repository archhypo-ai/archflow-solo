import { MessagePrimitive } from "@assistant-ui/react";
import { ChatMarkdownText } from "./ChatMarkdownText";

export function ChatAssistantMessage() {
  return (
    <MessagePrimitive.Root className="chat-message chat-message-assistant">
      <MessagePrimitive.Parts components={{ Text: ChatMarkdownText }} />
    </MessagePrimitive.Root>
  );
}
