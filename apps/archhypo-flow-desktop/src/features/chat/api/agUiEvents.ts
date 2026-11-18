import type { EventType } from "@ag-ui/core";
import type {
  RunErrorEvent,
  RunFinishedEvent,
  RunStartedEvent,
  TextMessageContentEvent,
  TextMessageEndEvent,
  TextMessageStartEvent,
  ToolCallArgsEvent,
  ToolCallEndEvent,
  ToolCallResultEvent,
  ToolCallStartEvent,
} from "@ag-ui/core";
import type { ChatStreamEvent } from "../types";

type CustomEvent<T extends ChatStreamEvent["type"]> = {
  type: EventType.CUSTOM;
  name: `archhypo.${T}`;
  value: Extract<ChatStreamEvent, { type: T }>;
};

type Completion = Pick<Extract<ChatStreamEvent, { type: "done" }>, "title" | "message">;

export type ArchHypoAgUiEvent =
  | RunStartedEvent
  | (RunFinishedEvent & { result?: Completion })
  | RunErrorEvent
  | TextMessageStartEvent
  | TextMessageContentEvent
  | TextMessageEndEvent
  | ToolCallStartEvent
  | ToolCallArgsEvent
  | ToolCallEndEvent
  | (ToolCallResultEvent & { content: string; metadata: { isError: boolean } })
  | CustomEvent<"conversation_started">
  | CustomEvent<"phase">;
