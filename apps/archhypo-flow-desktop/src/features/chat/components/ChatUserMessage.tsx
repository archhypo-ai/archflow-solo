import { MessagePrimitive } from "@assistant-ui/react";
import { ChatMarkdownText } from "./ChatMarkdownText";

export function ChatUserMessage() {
  return (
    <MessagePrimitive.Root className="chat-message chat-message-user">
      <div className="chat-message-bubble">
        <MessagePrimitive.Parts components={{ Text: ChatMarkdownText }} />
      </div>
    </MessagePrimitive.Root>
  );
}
