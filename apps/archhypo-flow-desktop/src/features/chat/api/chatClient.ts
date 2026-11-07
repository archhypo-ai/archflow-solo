import { getGlobalContext, getHitlEnabled } from "../../settings";
import type {
  ChatStreamEvent,
  HypothesisReviewDecision,
  TechnicalPlanReviewDecision,
} from "../types";

const API_BASE_URL = "http://127.0.0.1:8765";

export async function* streamChatMessage(
  threadId: string,
  message: string,
  language: "en" | "pt-BR",
  projectId: string | null,
  signal: AbortSignal,
  hypothesisReview?: HypothesisReviewDecision,
  technicalPlanReview?: TechnicalPlanReviewDecision,
  attachments?: Array<{ name: string; data: string; folder_id?: string; folder_name?: string }>,
): AsyncGenerator<ChatStreamEvent> {
  const global_context = await getGlobalContext();
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    signal,
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      thread_id: threadId,
      message,
      language,
      project_id: projectId,
      global_context,
      hitl_enabled: getHitlEnabled(),
      ...(attachments?.length ? { attachments } : {}),
      ...(hypothesisReview ? { hypothesis_review: hypothesisReview } : {}),
      ...(technicalPlanReview
        ? { technical_plan_review: technicalPlanReview }
        : {}),
    }),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Keep the HTTP status text if the error body is not JSON.
    }
    throw new Error(`Chat API error (${response.status}): ${detail}`);
  }
  if (!response.body) throw new Error("Chat stream has no response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let dataLines: string[] = [];

  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (line === "") {
          if (dataLines.length > 0) {
            yield parseStreamEvent(dataLines.join("\n"));
            dataLines = [];
          }
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).replace(/^ /, ""));
        }
      }

      if (done) {
        if (buffer.startsWith("data:")) {
          dataLines.push(buffer.slice(5).replace(/^ /, ""));
        }
        if (dataLines.length > 0) yield parseStreamEvent(dataLines.join("\n"));
        return;
      }
    }
  } finally {
    reader.releaseLock();
  }
}

function parseStreamEvent(data: string): ChatStreamEvent {
  const value: unknown = JSON.parse(data);
  if (
    !value ||
    typeof value !== "object" ||
    !("type" in value) ||
    !("protocol_version" in value) ||
    value.protocol_version !== 1 ||
    !("run_id" in value) ||
    typeof value.run_id !== "string" ||
    !("thread_id" in value) ||
    typeof value.thread_id !== "string"
  ) {
    throw new Error("Invalid chat stream event envelope");
  }

  const event = value as ChatStreamEvent;
  if (event.type === "error") throw new Error(event.message);
  if (
    ![
      "conversation_started",
      "phase",
      "tool_call_start",
      "tool_call_delta",
      "tool_result",
      "text_delta",
      "interrupt",
      "done",
    ].includes(event.type)
  ) {
    throw new Error("Unsupported chat stream event");
  }
  return event;
}
