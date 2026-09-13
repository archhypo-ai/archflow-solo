import {
  ActionBarPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAssistantState,
  useThread,
} from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-ui";
import { ArrowUp, Check, Copy, Plus, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useI18n } from "../../../i18n";

const MarkdownText = makeMarkdownText({
  className: "message-markdown",
});

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

function MessageCopyAction() {
  const { t } = useI18n();
  const hasCopyableText = useAssistantState(({ message }) =>
    message.parts.some((part) => part.type === "text"),
  );

  if (!hasCopyableText) return null;

  return (
    <div className="message-action-area">
      <ActionBarPrimitive.Root
        className="message-action-bar"
        autohide="always"
        autohideFloat="never"
      >
        <ActionBarPrimitive.Copy
          className="message-action-button"
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

function UserMessage() {
  return (
    <MessagePrimitive.Root className="message message-user" data-role="user">
      <div className="message-bubble">
        <MessagePrimitive.Parts components={{ Text: MarkdownText }} />
      </div>
      <MessageCopyAction />
    </MessagePrimitive.Root>
  );
}

function AssistantWorkingIndicator() {
  const { t } = useI18n();
  const isRunning = useAssistantState(
    ({ message }) => message.status?.type === "running",
  );

  if (!isRunning) return null;

  return (
    <span className="assistant-working-indicator" role="status">
      <span className="assistant-working-indicator-dot" aria-hidden="true">
        ●
      </span>
      <span>{t("chat.thinking")}</span>
    </span>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root
      className="message message-assistant"
      data-role="assistant"
    >
      <div className="message-content">
        <MessagePrimitive.Parts
          components={{
            Empty: AssistantWorkingIndicator,
            Text: MarkdownText,
          }}
        />
        <MessagePrimitive.Error>
          <div className="message-error">
            <ErrorPrimitive.Message />
          </div>
        </MessagePrimitive.Error>
      </div>
      <MessageCopyAction />
    </MessagePrimitive.Root>
  );
}

function Messages() {
  return (
    <div className="message-list">
      <ThreadPrimitive.Messages components={{ UserMessage, AssistantMessage }} />
    </div>
  );
}

function ChatViewport({ children, isEmpty }: { children: React.ReactNode; isEmpty: boolean }) {
  const [isScrolling, setIsScrolling] = useState(false);
  const scrollEndTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (scrollEndTimer.current) clearTimeout(scrollEndTimer.current);
    };
  }, []);

  const handleScroll = () => {
    setIsScrolling(true);
    if (scrollEndTimer.current) clearTimeout(scrollEndTimer.current);
    scrollEndTimer.current = setTimeout(() => {
      setIsScrolling(false);
      scrollEndTimer.current = null;
    }, 700);
  };

  return (
    <ThreadPrimitive.Viewport
      className={`chat-viewport${isEmpty ? " is-empty" : ""}${
        isScrolling ? " is-scrolling" : ""
      }`}
      onScroll={handleScroll}
    >
      {children}
    </ThreadPrimitive.Viewport>
  );
}

function ValidationDisclaimer() {
  const { t } = useI18n();
  return (
    <p className="chat-validation-disclaimer">
      {t("chat.validationDisclaimer")}
    </p>
  );
}

function Composer() {
  const { t } = useI18n();
  const isRunning = useThread((state) => state.isRunning);

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
        {!isRunning ? (
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
        ) : (
          <ComposerPrimitive.Cancel asChild>
            <button
              className="composer-button"
              aria-label={t("chat.stop")}
              title={t("chat.stop")}
              type="button"
            >
              <Square aria-hidden="true" />
            </button>
          </ComposerPrimitive.Cancel>
        )}
      </div>
    </ComposerPrimitive.Root>
  );
}

export function ArchwiseThread() {
  const isEmpty = useThread((state) => state.messages.length === 0);

  return (
    <ThreadPrimitive.Root className="aui-root chat-root">
      <ChatViewport isEmpty={isEmpty}>
        {isEmpty ? (
          <div className="chat-empty-state">
            <Welcome />
            <div className="chat-empty-composer">
              <Composer />
              <ValidationDisclaimer />
            </div>
          </div>
        ) : (
          <Messages />
        )}
        {!isEmpty && (
          <div className="chat-footer">
            <div className="chat-footer-content">
              <Composer />
              <ValidationDisclaimer />
            </div>
          </div>
        )}
      </ChatViewport>
    </ThreadPrimitive.Root>
  );
}
