import type { StoredToolCall } from "../conversations/types";

export type ChatStreamEvent =
  | { type: "phase"; phase: "thinking" | "answering" }
  | { type: "tool_call_start"; tool_call_id: string; name: string }
  | { type: "tool_call_delta"; tool_call_id: string; text: string }
  | {
      type: "tool_result";
      tool_call_id: string;
      output: unknown;
      is_error: boolean;
    }
  | { type: "text_delta"; text: string }
  | {
      type: "done";
      thread_id: string;
      title: string;
      message: string;
      tool_calls: StoredToolCall[];
    }
  | { type: "error"; message: string };
