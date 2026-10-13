import { MessagePrimitive, useAuiState } from "@assistant-ui/react";
import { ChatMarkdownText } from "./ChatMarkdownText";
import { ChatMessageActions } from "./ChatMessageActions";

export function ChatUserMessage() {
  const isReviewAction = useAuiState(
    ({ message }) => message.metadata.custom.isReviewAction,
  );
  if (isReviewAction) return null;

  return (
    <MessagePrimitive.Root className="chat-message chat-message-user">
      <div className="chat-message-bubble">
        <MessagePrimitive.Parts components={{ Text: ChatMarkdownText }} />
      </div>
      <ChatMessageActions />
    </MessagePrimitive.Root>
  );
}
