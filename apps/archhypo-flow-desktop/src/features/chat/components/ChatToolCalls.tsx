import {
  type ToolCallMessagePartComponent,
  useAuiState,
} from "@assistant-ui/react";
import {
  AlertCircle,
  Cog,
  ChevronRight,
  CircleCheck,
  LoaderCircle,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

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

export const ChatToolCall: ToolCallMessagePartComponent<ToolArgs, unknown> = ({
  toolName,
  args,
  argsText,
  result,
  status,
  isError,
  interrupt,
}) => {
  const { t } = useTranslation();
  const isRunning = status.type === "running";
  const isWaiting = status.type === "requires-action";
  const isFailed = isError || status.type === "incomplete";
  const target = toolTarget(args);

  return (
    <details className="chat-tool-call" data-status={status.type}>
      <summary className="chat-tool-call-summary">
        <ChevronRight className="chat-tool-call-chevron" aria-hidden="true" />
        <span className="chat-tool-call-icon">
          {isRunning && <LoaderCircle className="chat-tool-spinner" aria-hidden="true" />}
          {(isWaiting || isFailed) && <AlertCircle aria-hidden="true" />}
          {!isRunning && !isWaiting && !isFailed && <CircleCheck aria-hidden="true" />}
        </span>
        <span className="chat-tool-call-name">{formatToolName(toolName)}</span>
        {target && <span className="chat-tool-call-target">{target}</span>}
      </summary>
      <div className="chat-tool-call-details">
        {argsText && (
          <div>
            <span className="chat-tool-call-label">{t("chat.toolArguments")}</span>
            <pre>{formatToolValue(args)}</pre>
          </div>
        )}
        {result !== undefined && (
          <div>
            <span className="chat-tool-call-label">{t("chat.toolResult")}</span>
            <pre>{formatToolValue(result)}</pre>
          </div>
        )}
        {interrupt && <pre>{formatToolValue(interrupt.payload)}</pre>}
      </div>
    </details>
  );
};

export function ChatToolCallGroup({
  startIndex,
  endIndex,
  children,
}: {
  startIndex: number;
  endIndex: number;
  children?: ReactNode;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const count = endIndex - startIndex + 1;
  const isRunning = useAuiState(({ message }) =>
    message.parts
      .slice(startIndex, endIndex + 1)
      .some((part) => part.type === "tool-call" && part.status.type === "running"),
  );
  const label = t(count === 1 ? "chat.toolCall" : "chat.toolCalls", { count });

  useEffect(() => {
    if (isRunning) setOpen(true);
  }, [isRunning]);

  return (
    <div className="chat-tool-group">
      <button
        className="chat-tool-group-trigger"
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <ChevronRight
          className={`chat-tool-group-chevron${open ? " is-open" : ""}`}
          aria-hidden="true"
        />
        {isRunning && <Cog className="chat-tool-group-cog" aria-hidden="true" />}
        <span>{label}</span>
      </button>
      {open && <div className="chat-tool-group-content">{children}</div>}
    </div>
  );
}
