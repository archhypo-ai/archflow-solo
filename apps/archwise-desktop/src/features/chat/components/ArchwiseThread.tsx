import {
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useThread,
} from "@assistant-ui/react";
import { ArrowUp, Plus } from "lucide-react";
import { useI18n } from "../../../i18n";

function Welcome() {
  const { t } = useI18n();

  return (
    <section className="chat-welcome" aria-labelledby="welcome-title">
      <span className="chat-eyebrow">ARCHWISE</span>
      <h2 id="welcome-title">{t("chat.welcomeTitle")}</h2>
      <p>{t("chat.welcomeDescription")}</p>
    </section>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="message message-user">
      <div className="message-bubble">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="message message-assistant">
      <div className="message-content">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function Messages() {
  return (
    <div className="message-list">
      <ThreadPrimitive.Messages
        components={{ UserMessage, AssistantMessage }}
      />
    </div>
  );
}

function Composer() {
  const { t } = useI18n();

  return (
    <ComposerPrimitive.Root className="chat-composer">
      <ComposerPrimitive.Input
        className="chat-input"
        minRows={1}
        maxRows={7}
        placeholder={t("chat.inputPlaceholder")}
        aria-label={t("chat.message")}
      />
      <div className="composer-footer">
        <button
          className="composer-tool-button"
          aria-label={t("chat.addAttachment")}
          title={t("chat.addAttachment")}
          type="button"
        >
          <Plus aria-hidden="true" />
        </button>
        <ComposerPrimitive.Send asChild>
          <button
            className="composer-button"
            aria-label={t("chat.send")}
            title={t("chat.send")}
            type="button"
          >
            <ArrowUp aria-hidden="true" />
          </button>
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
}

export function ArchwiseThread() {
  const { t } = useI18n();
  const isEmpty = useThread((state) => state.messages.length === 0);

  return (
    <ThreadPrimitive.Root className="chat-root">
      <ThreadPrimitive.Viewport className="chat-viewport">
        {isEmpty ? <Welcome /> : <Messages />}
        <div className="chat-footer">
          <Composer />
          <p className="chat-validation-disclaimer">
            {t("chat.validationDisclaimer")}
          </p>
        </div>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
}
