import {
  AuiIf,
  ComposerPrimitive,
} from "@assistant-ui/react";
import { ArrowUp, Square } from "lucide-react";

type ChatComposerProps = {
  placeholder?: string;
  inputLabel?: string;
  hint?: string;
};

export function ChatComposer({
  placeholder = "Escreva uma mensagem...",
  inputLabel = "Mensagem",
  hint = "Enter para enviar · Shift+Enter para nova linha",
}: ChatComposerProps) {
  return (
    <ComposerPrimitive.Root className="chat-composer">
      <ComposerPrimitive.Input
        className="chat-composer-input"
        aria-label={inputLabel}
        placeholder={placeholder}
        minRows={1}
        maxRows={7}
      />
      <div className="chat-composer-footer">
        <span className="chat-composer-hint">{hint}</span>
        <AuiIf condition={(state) => state.thread.isRunning}>
          <ComposerPrimitive.Cancel asChild>
            <button
              className="chat-send-button is-cancel"
              type="button"
              aria-label="Interromper resposta"
              title="Interromper resposta"
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
              aria-label="Enviar mensagem"
              title="Enviar mensagem"
            >
              <ArrowUp size={18} aria-hidden="true" />
            </button>
          </ComposerPrimitive.Send>
        </AuiIf>
      </div>
    </ComposerPrimitive.Root>
  );
}
