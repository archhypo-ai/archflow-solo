type ChatStreamEventBase = {
  protocol_version: 1;
  run_id: string;
  thread_id: string;
};

export type HypothesisReviewDecision = {
  decision: "approved" | "rejected";
  reason?: string;
};

export type PendingHypothesisReview = {
  kind: "hypothesis_review";
  hypothesis: {
    uncertainty: string;
    title: string;
    statement: string;
    justification: string;
  };
};

export type ChatStreamEvent =
  | (ChatStreamEventBase & {
      type: "conversation_started";
      title: string;
      user_message: string;
      project_id: string | null;
    })
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
      type: "interrupt";
      interrupt_id: string;
      message: string;
      payload: PendingHypothesisReview | null;
    })
  | (ChatStreamEventBase & {
      type: "done";
      status: "completed";
      title: string;
      message: string;
    })
  | (ChatStreamEventBase & { type: "error"; message: string });
