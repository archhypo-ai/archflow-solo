import { useCallback, useEffect, useState } from "react";
import { useI18n } from "../../../i18n";
import type { Conversation } from "../types";

function newId() {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `local-${Date.now()}`;
}

export function useConversations() {
  const { language, t } = useI18n();
  const [conversations, setConversations] = useState<Conversation[]>(() => [
    {
      id: "demo-architecture",
      label: t("conversation.architectureDiscussion"),
      pinned: false,
    },
    {
      id: "demo-hypothesis",
      label: t("conversation.hypothesisEngineering"),
      pinned: true,
    },
  ]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | undefined
  >("demo-architecture");

  useEffect(() => {
    setConversations((current) =>
      current.map((conversation) => {
        if (conversation.id === "demo-architecture") {
          return {
            ...conversation,
            label: t("conversation.architectureDiscussion"),
          };
        }
        if (conversation.id === "demo-hypothesis") {
          return {
            ...conversation,
            label: t("conversation.hypothesisEngineering"),
          };
        }
        return conversation;
      }),
    );
  }, [language]);

  const newConversation = useCallback(() => {
    const conversation = {
      id: newId(),
      label: t("app.newConversation"),
      pinned: false,
    };
    setConversations((current) => [conversation, ...current]);
    setActiveConversationId(conversation.id);
  }, [t]);

  const selectConversation = useCallback((conversation: Conversation) => {
    setActiveConversationId(conversation.id);
  }, []);

  return {
    conversations,
    activeConversationId,
    newConversation,
    selectConversation,
  };
}
