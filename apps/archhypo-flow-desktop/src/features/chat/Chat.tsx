import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../i18n";
import { getConversation } from "./api/chatClient";
import { createChatModelAdapter } from "./adapters/chatModelAdapter";
import { ChatThread } from "./components/ChatThread";
import type { StoredChatMessage } from "./types";

type ChatProps = {
  threadId: string;
  language: AppLanguage;
  onConversationUpdated: (threadId: string, title: string) => void;
};

function toInitialMessages(
  threadId: string,
  messages: StoredChatMessage[],
): ThreadMessageLike[] {
  return messages.map((message, index) => ({
    id: `${threadId}-${index}`,
    role: message.role,
    content: [{ type: "text", text: message.content }],
    createdAt: new Date(),
  }));
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
            ? toInitialMessages(props.threadId, conversation.messages)
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
  onConversationUpdated,
  initialMessages,
}: LoadedChatProps) {
  const chatModel = useMemo(
    () =>
      createChatModelAdapter({
        threadId,
        language,
        onConversationUpdated,
      }),
    [threadId, language, onConversationUpdated],
  );
  const runtime = useLocalRuntime(chatModel, { initialMessages });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatThread />
    </AssistantRuntimeProvider>
  );
}
