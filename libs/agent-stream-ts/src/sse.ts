import type { AgentEvent, ChatStreamRequest } from "./models.js";

export class AgentStreamError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AgentStreamError";
  }
}

export function parseAgentEvent(data: string): AgentEvent {
  const value: unknown = JSON.parse(data);
  if (!isRecord(value) || value.protocol_version !== 1) {
    throw new AgentStreamError("Invalid agent stream protocol version");
  }
  if (
    typeof value.run_id !== "string" ||
    typeof value.thread_id !== "string" ||
    typeof value.type !== "string"
  ) {
    throw new AgentStreamError("Invalid agent stream event envelope");
  }

  switch (value.type) {
    case "phase":
      return requireFields(value, ["phase"]);
    case "text_delta":
      return requireFields(value, ["text"]);
    case "done":
      return requireFields(value, ["status"]);
    case "cancelled":
      return value as unknown as AgentEvent;
    case "error":
      return requireFields(value, ["message"]);
    case "tool_call_start":
      return requireFields(value, ["tool_call_id", "name"]);
    case "tool_call_delta":
      return requireFields(value, ["tool_call_id", "text"]);
    case "tool_result":
      return requireFields(value, ["tool_call_id", "output"]);
    case "interrupt":
      return requireFields(value, ["interrupt_id", "message"]);
    default:
      throw new AgentStreamError(`Unsupported agent stream event: ${value.type}`);
  }
}

export async function* readAgentStream(
  response: Response,
  signal?: AbortSignal,
): AsyncGenerator<AgentEvent> {
  if (!response.ok) {
    throw new AgentStreamError(`Agent stream returned HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new AgentStreamError("Agent stream response has no body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let dataLines: string[] = [];

  const emit = (): AgentEvent | undefined => {
    if (dataLines.length === 0) return undefined;
    const data = dataLines.join("\n");
    dataLines = [];
    return parseAgentEvent(data);
  };

  while (true) {
    if (signal?.aborted) return;
    const result = await reader.read();
    buffer += decoder.decode(result.value ?? new Uint8Array(), {
      stream: !result.done,
    });

    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line === "") {
        const event = emit();
        if (event) yield event;
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).replace(/^ /, ""));
      }
    }

    if (result.done) {
      if (buffer !== "") {
        if (buffer.startsWith("data:")) {
          dataLines.push(buffer.slice(5).replace(/^ /, ""));
        }
        buffer = "";
      }
      const event = emit();
      if (event) yield event;
      return;
    }
  }
}

export async function* streamChat(
  url: string,
  request: ChatStreamRequest,
  init: RequestInit = {},
): AsyncGenerator<AgentEvent> {
  const response = await fetch(url, {
    ...init,
    method: "POST",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
      ...init.headers,
    },
    body: JSON.stringify(request),
  });
  yield* readAgentStream(response, init.signal ?? undefined);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function requireFields<T extends Record<string, unknown>>(
  value: T,
  fields: string[],
): AgentEvent {
  if (fields.some((field) => !(field in value))) {
    throw new AgentStreamError("Invalid agent stream event payload");
  }
  return value as unknown as AgentEvent;
}
