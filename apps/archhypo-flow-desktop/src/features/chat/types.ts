type ChatStreamEventBase = {
  protocol_version: 1;
  run_id: string;
  thread_id: string;
};

export type ChatStreamEvent =
  | (ChatStreamEventBase & {
      type: "phase";
      phase: "thinking" | "answering";
    })
  | (ChatStreamEventBase & {
      type: "tool_call_start";
      tool_call_id: string;
      name: string;
    })
  | (ChatStreamEventBase & {
      type: "tool_call_delta";
      tool_call_id: string;
      text: string;
    })
  | (ChatStreamEventBase & {
      type: "tool_result";
      tool_call_id: string;
      output: unknown;
      is_error: boolean;
    })
  | (ChatStreamEventBase & { type: "text_delta"; text: string })
  | (ChatStreamEventBase & {
      type: "done";
      status: "completed";
      title: string;
      message: string;
    })
  | (ChatStreamEventBase & { type: "error"; message: string });
