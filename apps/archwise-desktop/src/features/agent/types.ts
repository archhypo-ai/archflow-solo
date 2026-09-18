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

export type BackendFolderContext = {
  context_id: string;
  thread_id: string;
  folder_name: string;
  file_count: number;
  total_bytes: number;
};

export type BackendThread = BackendThreadSummary & {
  messages: BackendThreadMessage[];
  folder_context: BackendFolderContext | null;
};

export type BackendActiveRun = {
  thread_id: string;
  run_id: string;
  status: "running";
};

export type BackendChatResponse = {
  thread_id: string;
  message: string;
  status: "completed";
};
