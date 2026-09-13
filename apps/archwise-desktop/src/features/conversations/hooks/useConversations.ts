import { useCallback, useState } from "react";
import type { Conversation } from "../types";

const initialConversations: Conversation[] = [
  {
    id: "demo-architecture",
    label: "Architecture discussion",
    pinned: false,
  },
  {
    id: "demo-hypothesis",
    label: "Hypothesis engineering",
    pinned: true,
  },
];

function newId() {
  return typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `local-${Date.now()}`;
}

export function useConversations() {
  const [conversations, setConversations] =
    useState<Conversation[]>(initialConversations);
  const [activeConversationId, setActiveConversationId] = useState<
    string | undefined
  >(initialConversations[0]?.id);

  const newConversation = useCallback(() => {
    const conversation = {
      id: newId(),
      label: "New conversation",
      pinned: false,
    };
    setConversations((current) => [conversation, ...current]);
    setActiveConversationId(conversation.id);
  }, []);

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
