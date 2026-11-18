import { CopilotChatView, CopilotKitProvider, useAgent } from "@copilotkit/react-core/v2";
import { EventType, type Message } from "@ag-ui/core";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../i18n";
import { getConversation, type StoredConversation } from "../conversations";
import type { Project } from "../projects/types";
import { archHypoAgent, streamChatMessage } from "./api/chatClient";
import { attachmentFolder } from "./adapters/documentAttachmentAdapter";
import { ChatComposer } from "./components/ChatComposer";
import { ChatWelcome } from "./components/ChatWelcome";
import { ARCHHYPO_ACTIVITY, ReviewActions, copilotActivityRenderers, type ChatDetails } from "./components/CopilotChatDetails";
import type { HumanReviewDecision, PendingHumanReview } from "./types";
import "@copilotkit/react-core/v2/styles.css";
import "./Chat.css";

type ChatProps = {
  threadId: string;
  language: AppLanguage;
  projectId: string | null;
  project: Project | null;
  projectLanding: boolean;
  projectLandingContent?: ReactNode;
  onConversationStarted: (
    threadId: string,
    title: string,
    userMessage: string,
    projectId: string | null,
  ) => void;
  onConversationUpdated: (
    threadId: string,
    title: string,
    preview: string,
    projectId: string | null,
  ) => void;
};

const agents = { archhypo: archHypoAgent };
const NoBuiltInComposer = () => null;

function details(id: string, content: ChatDetails): Message {
  return { id, role: "activity", activityType: ARCHHYPO_ACTIVITY, content };
}

function initialHistory(threadId: string, conversation: StoredConversation | null): Message[] {
  if (!conversation) return [];
  const result: Message[] = [];
  for (let index = 0; index <= conversation.messages.length; index++) {
    for (const [reviewIndex, review] of (conversation.completedReviews ?? []).entries()) {
      if (Math.min(Math.max(0, review.after_message_count), conversation.messages.length) === index) {
        result.push(details(`${threadId}-review-${reviewIndex}`, { completedReview: review }));
      }
    }
    const entry = conversation.messages[index];
    if (!entry) continue;
    const id = `${threadId}-${index}`;
    const files = entry.attachments?.map(({ name }) => `📎 ${name}`).join("\n");
    const content = [entry.content, files].filter(Boolean).join("\n\n");
    if (content) result.push({ id, role: entry.role, content });
    if (entry.a2ui_messages?.length || entry.tool_calls?.length) {
      result.push(details(`${id}-details`, {
        a2uiSurface: entry.a2ui_messages,
        tools: entry.tool_calls?.map(({ name }) => name),
      }));
    }
  }
  return result;
}

export function Chat(props: ChatProps) {
  return (
    <CopilotKitProvider selfManagedAgents={agents} agentId="archhypo" enableInspector={false}
      showIntelligenceIndicator={false} renderActivityMessages={copilotActivityRenderers}>
      <ChatSession key={props.threadId} {...props} />
    </CopilotKitProvider>
  );
}

function ChatSession(props: ChatProps) {
  const { t } = useTranslation();
  const { agent, isReady } = useAgent({ agentId: "archhypo" });
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [pending, setPending] = useState<PendingHumanReview | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const activeRun = useRef<AbortController | null>(null);
  const { threadId, language, projectId } = props;

  useEffect(() => {
    let active = true;
    void getConversation(threadId).then((conversation) => {
      if (!active) return;
      setMessages(initialHistory(threadId, conversation));
      setPending(conversation?.pendingHypothesisReview ?? conversation?.pendingTechnicalPlanReview ?? null);
      setError("");
    }).catch(() => { if (active) setError(t("chat.loadError")); });
    return () => { active = false; activeRun.current?.abort(); };
  }, [threadId, reload]);

  async function send(text: string, files: File[], review?: PendingHumanReview, decision?: HumanReviewDecision) {
    if (activeRun.current || !messages || (pending && !review)) return false;
    const controller = new AbortController();
    activeRun.current = controller;
    setRunning(true);
    setError("");
    const id = crypto.randomUUID();
    let answer = "";
    let operations: unknown[] = [];
    const tools: string[] = [];
    let terminal = false;
    const history = [...messages];
    const publish = () => {
      if (controller.signal.aborted) return;
      setMessages([
        ...history,
        ...(answer ? [{ id, role: "assistant" as const, content: answer }] : []),
        ...(operations.length || tools.length ? [details(`${id}-details`, {
          a2uiSurface: operations.length ? operations : undefined, tools: [...tools],
        })] : []),
      ]);
    };
    try {
      const attachments = await Promise.all(files.map(async (file) => {
        const url = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result));
          reader.onerror = () => reject(new Error(t("chat.attachmentAddError")));
          reader.readAsDataURL(file);
        });
        const folder = attachmentFolder(file);
        return { name: file.name, data: url.split(",", 2)[1], ...(folder ? {
          folder_id: folder.id, folder_name: folder.name,
        } : {}) };
      }));
      if (controller.signal.aborted) return false;
      if (!review) {
        history.push({ id: `${id}-user`, role: "user", content: [text, files.map(({ name }) => `📎 ${name}`).join("\n")].filter(Boolean).join("\n\n") });
        publish();
      }
      for await (const event of streamChatMessage(
        threadId, text, language, projectId, controller.signal,
        review?.kind === "hypothesis_review" ? decision : undefined,
        review?.kind === "technical_plan_review" ? decision : undefined,
        attachments, review?.interrupt_id, isReady ? agent : archHypoAgent,
      )) {
        switch (event.type) {
          case EventType.CUSTOM:
            if (event.name === "archhypo.conversation_started") {
              const data = event.value;
              if (data.user_message.trim() || attachments.length) {
                props.onConversationStarted(data.thread_id, data.title, data.user_message, data.project_id);
              }
            } else if (event.name === "archhypo.a2ui") {
              const batch = Array.isArray(event.value) ? event.value : [event.value];
              if (operations.length + batch.length <= 200) operations = [...operations, ...batch];
              publish();
            }
            break;
          case EventType.TOOL_CALL_START:
            tools.push(event.toolCallName);
            publish();
            break;
          case EventType.TEXT_MESSAGE_CONTENT:
            answer += event.delta;
            publish();
            break;
          case EventType.RUN_ERROR:
            throw new Error(event.message);
          case EventType.RUN_FINISHED: {
            terminal = true;
            const interrupt = event.outcome?.type === "interrupt" ? event.outcome.interrupts[0] : undefined;
            const next = interrupt?.metadata?.archhypoReview as PendingHumanReview | undefined;
            if (review && decision?.decision === "approved") {
              history.push(details(`${id}-approved`, { completedReview: { review } }));
            }
            setPending(next && interrupt ? { ...next, interrupt_id: interrupt.id } : null);
            if (event.result) {
              answer = event.result.message;
              props.onConversationUpdated(event.threadId, event.result.title, answer, projectId);
            }
            publish();
            break;
          }
        }
      }
      if (!terminal && !controller.signal.aborted) throw new Error(t("chat.loadError"));
      return terminal;
    } catch (cause) {
      if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : t("chat.loadError"));
      return false;
    } finally {
      if (activeRun.current === controller) {
        activeRun.current = null;
        setRunning(false);
      }
    }
  }

  if (!messages) return (
    <div className="chat-runtime-state" role="status">
      {error ? <><p>{error}</p><button type="button" onClick={() => setReload((n) => n + 1)}>{t("chat.retry")}</button></> : t("chat.loading")}
    </div>
  );

  const composer = <ChatComposer running={running} disabled={Boolean(pending)}
    onSend={send} onStop={() => activeRun.current?.abort()} />;
  const visible = [
    ...messages,
    ...(pending ? [details(pending.interrupt_id ?? "pending", {
      hypothesisReview: pending.kind === "hypothesis_review" ? pending : undefined,
      technicalPlanReview: pending.kind === "technical_plan_review" ? pending : undefined,
    })] : []),
    ...(error ? [details("chat-error", { error })] : []),
  ];
  return (
    <ReviewActions.Provider value={{ running, submit: (review, decision) => { void send("", [], review, decision); } }}>
      <div className={visible.length || running ? "archhypo-copilot-session"
        : `chat-empty-state${props.projectLanding ? " is-project-landing" : ""}`}>
        <div className={visible.length || running ? "archhypo-copilot-transcript" : undefined}>
          {visible.length || running ? (
            <CopilotChatView className="archhypo-copilot-chat" messages={visible} isRunning={running}
              welcomeScreen={false} input={NoBuiltInComposer}
              messageView={{ className: "archhypo-message-list" }} />
          ) : <ChatWelcome project={props.project} />}
        </div>
        <div className={visible.length || running ? "archhypo-copilot-composer" : "chat-empty-composer"}>
          {pending && <div className="chat-review-paused">
            <p role="status">{t("chat.reviewPaused")}</p>
            <button type="button" onClick={() => {
              const review = document.getElementById("chat-pending-review");
              review?.focus({ preventScroll: true });
              review?.scrollIntoView({ block: "nearest" });
            }}>{t("chat.goToReview")}</button>
          </div>}
          {composer}
        </div>
        {!visible.length && !running && props.projectLanding && props.projectLandingContent}
      </div>
    </ReviewActions.Provider>
  );
}
