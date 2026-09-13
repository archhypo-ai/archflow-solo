export type BackendThreadSummary = {
  thread_id: string;
  title: string;
  message_count: number;
  pinned: boolean;
};

export type BackendThreadMessage = {
  role: "user" | "assistant";
  content: string;
};

export type BackendThread = BackendThreadSummary & {
  messages: BackendThreadMessage[];
};

export type BackendChatResponse = {
  thread_id: string;
  message: string;
  status: "completed";
};
