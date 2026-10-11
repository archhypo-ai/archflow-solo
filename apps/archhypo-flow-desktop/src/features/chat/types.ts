export type StoredChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ConversationSummary = {
  threadId: string;
  title: string;
  messageCount: number;
  updatedAt: string;
  pinned: boolean;
  projectId: string | null;
  preview: string;
};

export type StoredConversation = ConversationSummary & {
  messages: StoredChatMessage[];
};

export type ChatTurnResponse = {
  thread_id: string;
  title: string;
  message: string;
};
