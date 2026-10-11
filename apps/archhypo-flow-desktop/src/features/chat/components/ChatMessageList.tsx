import { ThreadPrimitive } from "@assistant-ui/react";
import { ChatAssistantMessage } from "./ChatAssistantMessage";
import { ChatUserMessage } from "./ChatUserMessage";

export function ChatMessageList() {
  return (
    <div className="chat-message-list">
      <ThreadPrimitive.Messages
        components={{
          UserMessage: ChatUserMessage,
          AssistantMessage: ChatAssistantMessage,
        }}
      />
    </div>
  );
}
