import type {
  PendingHypothesisReview,
  PendingTechnicalPlanReview,
  CompletedHumanReview,
} from "../chat/types";

export type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue };

export type StoredToolCall = {
  id: string;
  name: string;
  args: { [key: string]: JsonValue };
  result: JsonValue | null;
  is_error: boolean;
};

export type StoredChatMessage = {
  role: "user" | "assistant";
  content: string;
  tool_calls?: StoredToolCall[];
  attachments?: Array<{ name: string; size_bytes?: number; folder_id?: string; folder_name?: string }>;
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
  pendingHypothesisReview?: PendingHypothesisReview | null;
  pendingTechnicalPlanReview?: PendingTechnicalPlanReview | null;
  completedReviews?: CompletedHumanReview[];
};
