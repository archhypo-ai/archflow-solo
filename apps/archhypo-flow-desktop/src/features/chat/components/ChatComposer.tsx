import { AuiIf, ComposerPrimitive } from "@assistant-ui/react";
import { ArrowUp, Square } from "lucide-react";
import { useTranslation } from "react-i18next";

type ChatComposerProps = {
  placeholder?: string;
  inputLabel?: string;
};

export function ChatComposer({ placeholder, inputLabel }: ChatComposerProps) {
  const { t } = useTranslation();

  return (
    <ComposerPrimitive.Root className="chat-composer">
      <ComposerPrimitive.Input
        className="chat-composer-input"
        aria-label={inputLabel ?? t("chat.messageLabel")}
        placeholder={placeholder ?? t("chat.messagePlaceholder")}
        minRows={1}
        maxRows={7}
      />
      <div className="chat-composer-footer">
        <AuiIf condition={(state) => state.thread.isRunning}>
          <ComposerPrimitive.Cancel asChild>
            <button
              className="chat-send-button is-cancel"
              type="button"
              aria-label={t("chat.stopResponse")}
              title={t("chat.stopResponse")}
            >
              <Square size={16} aria-hidden="true" />
            </button>
          </ComposerPrimitive.Cancel>
        </AuiIf>
        <AuiIf condition={(state) => !state.thread.isRunning}>
          <ComposerPrimitive.Send asChild>
            <button
              className="chat-send-button"
              type="button"
              aria-label={t("chat.sendMessage")}
              title={t("chat.sendMessage")}
            >
              <ArrowUp size={18} aria-hidden="true" />
            </button>
          </ComposerPrimitive.Send>
        </AuiIf>
      </div>
    </ComposerPrimitive.Root>
  );
}
