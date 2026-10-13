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
import { ChatThread } from "./components/ChatThread";
import type { PendingHypothesisReview } from "./types";

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
  pendingReview: PendingHypothesisReview | null | undefined,
): ThreadMessageLike[] {
  const initialMessages: ThreadMessageLike[] = messages.map((message, index) => ({
    id: `${threadId}-${index}`,
    role: message.role,
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
      ...(message.content ? [{ type: "text" as const, text: message.content }] : []),
    ],
    createdAt: new Date(),
  }));
  if (pendingReview) {
    initialMessages.push({
      id: `${threadId}-pending-hypothesis-review`,
      role: "assistant",
      content: [],
      metadata: { custom: { hypothesisReview: pendingReview } },
      createdAt: new Date(),
    });
  }
  return initialMessages;
}

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
                conversation.pendingHypothesisReview,
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

  return <LoadedChat {...props} initialMessages={initialMessages} />;
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
  const chatModel = useMemo(
    () =>
      createChatModelAdapter({
        threadId,
        language,
        projectId,
        onConversationStarted,
        onConversationUpdated,
      }),
    [
      threadId,
      language,
      projectId,
      onConversationStarted,
      onConversationUpdated,
    ],
  );
  const runtime = useLocalRuntime(chatModel, { initialMessages });

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
