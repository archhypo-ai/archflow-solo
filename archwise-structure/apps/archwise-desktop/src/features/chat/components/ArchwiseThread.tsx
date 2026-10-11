import {
  ActionBarPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  type ToolCallMessagePartComponent,
  useAssistantState,
  useThread,
} from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-ui";
import remarkGfm from "remark-gfm";
import {
  AlertCircle,
  ArrowUp,
  Check,
  CircleCheck,
  ChevronRight,
  Cog,
  Copy,
  FolderOpen,
  LoaderCircle,
  Plus,
  Square,
  X,
} from "lucide-react";
import { type ChangeEvent, useEffect, useRef, useState } from "react";
import type { BackendFolderContext } from "../../agent";
import { Menu, MenuContent, MenuItem } from "../../../components/overlay/Menu";
import { useToast } from "../../../components/feedback";
import { isTauriDesktop, pickNativeFolder } from "../folderPicker";
import { useI18n } from "../../../i18n";

const MarkdownText = makeMarkdownText({
  className: "message-markdown",
  remarkPlugins: [remarkGfm],
});

type ToolArgs = Record<string, unknown>;

function formatToolName(name: string) {
  return name.split("_").join(" ");
}

function toolTarget(args: ToolArgs) {
  for (const key of ["path", "file_path", "pattern", "query", "command"]) {
    const value = args[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return "";
}

function formatToolValue(value: unknown) {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

const ArchwiseToolUI: ToolCallMessagePartComponent<ToolArgs, unknown> = ({
  toolName,
  args,
  argsText,
  result,
  status,
  isError,
  interrupt,
}) => {
  const { t } = useI18n();
  const isRunning = status.type === "running";
  const isWaiting = status.type === "requires-action";
  const isFailed = isError || status.type === "incomplete";
  const target = toolTarget(args);

  return (
    <details className="message-tool-call" data-status={status.type}>
      <summary className="message-tool-call-summary">
        <ChevronRight className="message-tool-call-chevron" aria-hidden="true" />
        <span className="message-tool-call-icon">
          {isRunning && (
            <LoaderCircle className="message-tool-spinner" aria-hidden="true" />
          )}
          {isWaiting && <AlertCircle aria-hidden="true" />}
          {isFailed && <AlertCircle aria-hidden="true" />}
          {!isRunning && !isWaiting && !isFailed && (
            <CircleCheck aria-hidden="true" />
          )}
        </span>
        <span className="message-tool-call-name">{formatToolName(toolName)}</span>
        {target && <span className="message-tool-call-target">{target}</span>}
      </summary>
      <div className="message-tool-call-details">
        {argsText && (
          <div>
            <span className="message-tool-call-label">
              {t("chat.toolArguments")}
            </span>
            <pre>{formatToolValue(args)}</pre>
          </div>
        )}
        {result !== undefined && (
          <div>
            <span className="message-tool-call-label">
              {t("chat.toolResult")}
            </span>
            <pre>{formatToolValue(result)}</pre>
          </div>
        )}
        {interrupt && <pre>{formatToolValue(interrupt.payload)}</pre>}
      </div>
    </details>
  );
};

function ToolCallGroup({
  startIndex,
  endIndex,
  children,
}: {
  startIndex: number;
  endIndex: number;
  children?: React.ReactNode;
}) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const count = endIndex - startIndex + 1;
  const isRunning = useAssistantState(({ message }) =>
    message.parts
      .slice(startIndex, endIndex + 1)
      .some((part) => part.type === "tool-call" && part.status.type === "running"),
  );
  const label = t(count === 1 ? "chat.toolCall" : "chat.toolCalls", { count });

  return (
    <div className="message-tool-group">
      <button
        className="message-tool-group-trigger"
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ChevronRight
          className={`message-tool-group-chevron${open ? " is-open" : ""}`}
          aria-hidden="true"
        />
        {isRunning && (
          <Cog className="message-tool-group-cog" aria-hidden="true" />
        )}
        <span>{label}</span>
      </button>
      {open && <div className="message-tool-group-content">{children}</div>}
    </div>
  );
}

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
  const phase = useAssistantState(({ message }) =>
    typeof message.metadata.custom.phase === "string"
      ? message.metadata.custom.phase
      : "thinking",
  );

  if (!isRunning) return null;

  const label = phase === "answering" ? t("chat.answering") : t("chat.thinking");

  return (
    <span className="assistant-working-indicator" role="status">
      <span className="assistant-working-indicator-dot" aria-hidden="true">
        ●
      </span>
      <span>{label}</span>
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
            Text: MarkdownText,
            ToolGroup: ToolCallGroup,
            tools: { Fallback: ArchwiseToolUI },
          }}
        />
        <AssistantWorkingIndicator />
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

type ComposerProps = {
  folderContext: BackendFolderContext | null;
  onFolderSelected: (folderName: string, files: File[]) => Promise<void>;
  onFolderPathSelected: (folderPath: string) => Promise<void>;
  onFolderRemoved: () => Promise<void>;
};

function Composer({
  folderContext,
  onFolderSelected,
  onFolderPathSelected,
  onFolderRemoved,
}: ComposerProps) {
  const { t } = useI18n();
  const toast = useToast();
  const isRunning = useThread((state) => state.isRunning);
  const [menuOpen, setMenuOpen] = useState(false);
  const [isAttaching, setIsAttaching] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleFolderRemove = async () => {
    setIsRemoving(true);
    try {
      await onFolderRemoved();
    } catch {
      toast.error(t("chat.folderRemoveError"));
    } finally {
      setIsRemoving(false);
    }
  };

  const handleFolderPicker = async () => {
    setMenuOpen(false);
    setIsAttaching(true);
    try {
      if (isTauriDesktop()) {
        const folderPath = await pickNativeFolder();
        if (folderPath) await onFolderPathSelected(folderPath);
      } else {
        folderInputRef.current?.click();
      }
    } catch {
      toast.error(t("chat.folderAttachError"));
    } finally {
      setIsAttaching(false);
    }
  };

  const handleFolderChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.currentTarget.files ?? []);
    const firstPath = files[0]?.webkitRelativePath || files[0]?.name || "";
    const folderName = firstPath.split("/")[0];
    event.currentTarget.value = "";
    if (!folderName || files.length === 0) return;

    setMenuOpen(false);
    setIsAttaching(true);
    try {
      await onFolderSelected(folderName, files);
    } catch {
      toast.error(t("chat.folderAttachError"));
    } finally {
      setIsAttaching(false);
    }
  };

  return (
    <ComposerPrimitive.Root className="chat-composer">
      <input
        ref={folderInputRef}
        className="chat-folder-input"
        type="file"
        multiple
        {...({ webkitdirectory: "", directory: "" } as Record<string, string>)}
        onChange={(event) => void handleFolderChange(event)}
        aria-hidden="true"
        tabIndex={-1}
      />
      <ComposerPrimitive.Input
        className="chat-input"
        minRows={1}
        maxRows={7}
        placeholder={t("chat.inputPlaceholder")}
        aria-label={t("chat.message")}
      />
      <div className="composer-footer">
        <div className="composer-tools">
          <Menu open={menuOpen} onOpenChange={setMenuOpen}>
            <button
              className="composer-tool-button"
              aria-label={t("chat.addAttachment")}
              title={t("chat.addAttachment")}
              type="button"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <Plus aria-hidden="true" />
            </button>
            <MenuContent open={menuOpen} className="composer-attachment-menu">
              <MenuItem
                icon={<FolderOpen aria-hidden="true" />}
                label={
                  isAttaching
                    ? t("chat.attachingFolder")
                    : t("chat.addFolder")
                }
                disabled={isAttaching}
                onClick={() => void handleFolderPicker()}
              />
            </MenuContent>
          </Menu>
          {folderContext && (
            <button
              className="composer-folder-context"
              type="button"
              aria-label={t("chat.removeFolder")}
              title={t("chat.removeFolder")}
              disabled={isAttaching || isRemoving}
              onClick={() => void handleFolderRemove()}
            >
              <FolderOpen aria-hidden="true" />
              <span>{folderContext.folder_name}</span>
              <X aria-hidden="true" />
            </button>
          )}
        </div>
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

type ArchwiseThreadProps = {
  folderContext: BackendFolderContext | null;
  onFolderSelected: (folderName: string, files: File[]) => Promise<void>;
  onFolderPathSelected: (folderPath: string) => Promise<void>;
  onFolderRemoved: () => Promise<void>;
};

export function ArchwiseThread({
  folderContext,
  onFolderSelected,
  onFolderPathSelected,
  onFolderRemoved,
}: ArchwiseThreadProps) {
  const isEmpty = useThread((state) => state.messages.length === 0);
  const composer = (
    <Composer
      folderContext={folderContext}
      onFolderSelected={onFolderSelected}
      onFolderPathSelected={onFolderPathSelected}
      onFolderRemoved={onFolderRemoved}
    />
  );

  return (
    <ThreadPrimitive.Root className="aui-root chat-root">
      <ChatViewport isEmpty={isEmpty}>
        {isEmpty ? (
          <div className="chat-empty-state">
            <Welcome />
            <div className="chat-empty-composer">
              {composer}
              <ValidationDisclaimer />
            </div>
          </div>
        ) : (
          <Messages />
        )}
        {!isEmpty && (
          <div className="chat-footer">
            <div className="chat-footer-content">
              {composer}
              <ValidationDisclaimer />
            </div>
          </div>
        )}
      </ChatViewport>
    </ThreadPrimitive.Root>
  );
}
