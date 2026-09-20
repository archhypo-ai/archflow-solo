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

export type AgentStreamEventBase = {
  protocol_version: 1;
  run_id: string;
  thread_id: string;
};

export type AgentStreamEvent = AgentStreamEventBase &
  (
    | { type: "phase"; phase: string }
    | { type: "text_delta"; text: string }
    | { type: "done"; status: "completed" }
    | { type: "cancelled"; status: "cancelled"; reason?: string | null }
    | { type: "error"; message: string }
    | { type: "tool_call_start"; tool_call_id: string; name: string }
    | { type: "tool_call_delta"; tool_call_id: string; text: string }
    | { type: "tool_result"; tool_call_id: string; output: unknown }
    | {
        type: "interrupt";
        interrupt_id: string;
        message: string;
        payload?: Record<string, unknown> | null;
      }
  );
