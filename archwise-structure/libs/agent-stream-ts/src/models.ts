/** Wire models for the ArchWise agent stream protocol. */

export type AgentEventBase = {
  protocol_version: 1;
  run_id: string;
  thread_id: string;
};

export type PhaseEvent = AgentEventBase & {
  type: "phase";
  phase: string;
};

export type TextDeltaEvent = AgentEventBase & {
  type: "text_delta";
  text: string;
};

export type DoneEvent = AgentEventBase & {
  type: "done";
  status: "completed";
};

export type CancelledEvent = AgentEventBase & {
  type: "cancelled";
  status: "cancelled";
  reason?: string | null;
};

export type ErrorEvent = AgentEventBase & {
  type: "error";
  message: string;
};

export type ToolCallStartEvent = AgentEventBase & {
  type: "tool_call_start";
  tool_call_id: string;
  name: string;
};

export type ToolCallDeltaEvent = AgentEventBase & {
  type: "tool_call_delta";
  tool_call_id: string;
  text: string;
};

export type ToolResultEvent = AgentEventBase & {
  type: "tool_result";
  tool_call_id: string;
  output: unknown;
  is_error?: boolean;
};

export type InterruptEvent = AgentEventBase & {
  type: "interrupt";
  interrupt_id: string;
  message: string;
  payload?: Record<string, unknown> | null;
};

export type AgentEvent =
  | PhaseEvent
  | TextDeltaEvent
  | DoneEvent
  | CancelledEvent
  | ErrorEvent
  | ToolCallStartEvent
  | ToolCallDeltaEvent
  | ToolResultEvent
  | InterruptEvent;

export type ChatStreamRequest = {
  thread_id: string;
  message: string;
  run_id?: string;
  workspace_id?: string;
  project_id?: string;
  user_id?: string;
};
