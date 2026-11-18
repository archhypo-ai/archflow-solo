import { CopilotKitProvider, useAgent } from "@copilotkit/react-core/v2";
import { archHypoAgent } from "./api/chatClient";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../i18n";
import { getConversation, type StoredChatMessage } from "../conversations";
import type { Project } from "../projects/types";
import { createChatModelAdapter } from "./adapters/chatModelAdapter";
import { DocumentAttachmentAdapter } from "./adapters/documentAttachmentAdapter";
import { ChatThread } from "./components/ChatThread";
import type {
  CompletedHumanReview,
  PendingHypothesisReview,
  PendingTechnicalPlanReview,
} from "./types";

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

function toInitialMessages(
  threadId: string,
  messages: StoredChatMessage[],
  completedReviews: CompletedHumanReview[],
  pendingHypothesisReview: PendingHypothesisReview | null | undefined,
  pendingTechnicalPlanReview: PendingTechnicalPlanReview | null | undefined,
): ThreadMessageLike[] {
  const reviewsByMessageCount = new Map<number, CompletedHumanReview[]>();
  for (const review of completedReviews) {
    const position = Math.min(
      Math.max(0, review.after_message_count),
      messages.length,
    );
    const reviews = reviewsByMessageCount.get(position) ?? [];
    reviews.push(review);
    reviewsByMessageCount.set(position, reviews);
  }

  const initialMessages: ThreadMessageLike[] = [];
  for (let index = 0; index <= messages.length; index += 1) {
    for (const review of reviewsByMessageCount.get(index) ?? []) {
      initialMessages.push({
        id: `${threadId}-completed-review-${initialMessages.length}`,
        role: "assistant",
        content: [],
        metadata: { custom: { completedHumanReview: review } },
        createdAt: new Date(),
      });
    }
    const message = messages[index];
    if (!message) continue;
    initialMessages.push({
      id: `${threadId}-${index}`,
      role: message.role,
      ...(message.role === "user" ? {
        metadata: { custom: {
          attachmentSizes: (message.attachments ?? []).map((attachment) => attachment.size_bytes ?? null),
          attachmentFolders: (message.attachments ?? []).map((attachment) => (
            attachment.folder_id && attachment.folder_name
              ? { id: attachment.folder_id, name: attachment.folder_name }
              : null
          )),
        } },
        attachments: (message.attachments ?? []).map((attachment, attachmentIndex) => ({
          id: `${threadId}-${index}-attachment-${attachmentIndex}`,
          type: "document" as const,
          name: attachment.name,
          contentType: "application/octet-stream",
          status: { type: "complete" as const },
          content: [],
        })),
      } : message.a2ui_messages?.length ? {
        metadata: { custom: { a2uiSurface: message.a2ui_messages } },
      } : {}),
      content: [
        ...(message.role === "assistant"
          ? (message.tool_calls ?? []).map((call) => ({
              type: "tool-call" as const,
              toolCallId: call.id,
              toolName: call.name,
              args: call.args,
              argsText: JSON.stringify(call.args),
              result: call.result,
              isError: call.is_error,
            }))
          : []),
        ...(message.content
          ? [{ type: "text" as const, text: message.content }]
          : []),
      ],
      createdAt: new Date(),
    });
  }
  if (pendingHypothesisReview) {
    initialMessages.push({
      id: `${threadId}-pending-hypothesis-review`,
      role: "assistant",
      content: [],
      metadata: { custom: { hypothesisReview: pendingHypothesisReview } },
      createdAt: new Date(),
    });
  }
  if (pendingTechnicalPlanReview) {
    initialMessages.push({
      id: `${threadId}-pending-technical-plan-review`,
      role: "assistant",
      content: [],
      metadata: { custom: { technicalPlanReview: pendingTechnicalPlanReview } },
      createdAt: new Date(),
    });
  }
  return initialMessages;
}

const chatAgents = { archhypo: archHypoAgent };

export function Chat(props: ChatProps) {
  const { t } = useTranslation();
  const [initialMessages, setInitialMessages] =
    useState<ThreadMessageLike[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    setInitialMessages(null);
    setLoadError(false);

    void getConversation(props.threadId)
      .then((conversation) => {
        if (!active) return;
        setInitialMessages(
          conversation
            ? toInitialMessages(
                props.threadId,
                conversation.messages,
                conversation.completedReviews ?? [],
                conversation.pendingHypothesisReview,
                conversation.pendingTechnicalPlanReview,
              )
            : [],
        );
      })
      .catch(() => {
        if (active) setLoadError(true);
      });

    return () => {
      active = false;
    };
  }, [props.threadId, reloadKey]);

  if (initialMessages === null) {
    return (
      <div className="chat-runtime-state" role="status">
        {loadError ? (
          <>
            <p>{t("chat.loadError")}</p>
            <button type="button" onClick={() => setReloadKey((key) => key + 1)}>
              {t("chat.retry")}
            </button>
          </>
        ) : (
          t("chat.loading")
        )}
      </div>
    );
  }

  return (
    <CopilotKitProvider selfManagedAgents={chatAgents} agentId="archhypo" enableInspector={false}>
      <LoadedChat key={props.threadId} {...props} initialMessages={initialMessages} />
    </CopilotKitProvider>
  );
}

type LoadedChatProps = ChatProps & {
  initialMessages: ThreadMessageLike[];
};

function LoadedChat({
  threadId,
  language,
  projectId,
  project,
  projectLanding,
  projectLandingContent,
  onConversationStarted,
  onConversationUpdated,
  initialMessages,
}: LoadedChatProps) {
  const { agent, isReady } = useAgent({ agentId: "archhypo" });
  const chatModel = useMemo(
    () =>
      createChatModelAdapter({
        agent: isReady ? agent : archHypoAgent,
        threadId,
        language,
        projectId,
        onConversationStarted,
        onConversationUpdated,
      }),
    [
      agent,
      isReady,
      threadId,
      language,
      projectId,
      onConversationStarted,
      onConversationUpdated,
    ],
  );
  const attachmentAdapter = useMemo(() => new DocumentAttachmentAdapter(), []);
  const runtime = useLocalRuntime(chatModel, {
    initialMessages, adapters: { attachments: attachmentAdapter },
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatThread
        project={project}
        projectLanding={projectLanding}
        projectLandingContent={projectLandingContent}
      />
    </AssistantRuntimeProvider>
  );
}
