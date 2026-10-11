import { ActionBarPrimitive, MessagePrimitive } from "@assistant-ui/react";
import { Check, Copy } from "lucide-react";
import { useTranslation } from "react-i18next";

export function ChatMessageActions() {
  const { t } = useTranslation();
  return (
    <div className="chat-message-actions">
      <ActionBarPrimitive.Root
        className="chat-message-action-bar"
        autohide="always"
        autohideFloat="never"
      >
        <ActionBarPrimitive.Copy
          className="chat-message-action-button"
          aria-label={t("chat.copyMessage")}
          title={t("chat.copyMessage")}
        >
          <MessagePrimitive.If copied>
            <Check aria-hidden="true" />
          </MessagePrimitive.If>
          <MessagePrimitive.If copied={false}>
            <Copy aria-hidden="true" />
          </MessagePrimitive.If>
        </ActionBarPrimitive.Copy>
      </ActionBarPrimitive.Root>
    </div>
  );
}
