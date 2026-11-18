import { getGlobalContext, getHitlEnabled } from "../../settings";
import type {
  HypothesisReviewDecision,
  TechnicalPlanReviewDecision,
} from "../types";

import type { ArchHypoAgUiEvent } from "./agUiEvents";

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
  interruptId?: unknown,
): AsyncGenerator<ArchHypoAgUiEvent> {
  const decision = hypothesisReview ?? technicalPlanReview;
  if (decision && (typeof interruptId !== "string" || !interruptId)) {
    throw new Error("Missing review interrupt ID. Reload the conversation and retry.");
  }
  const global_context = await getGlobalContext();
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    signal,
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      threadId,
      runId: crypto.randomUUID(),
      messages: message ? [{ id: crypto.randomUUID(), role: "user", content: message }] : [],
      state: {},
      tools: [],
      context: [],
      ...(decision ? { resume: [{
        interruptId,
        status: "resolved",
        payload: {
          kind: hypothesisReview ? "hypothesis_review" : "technical_plan_review",
          ...decision,
        },
      }] } : {}),
      forwardedProps: {
        archhypo: {
          language,
          project_id: projectId,
          global_context,
          hitl_enabled: getHitlEnabled(),
          ...(attachments?.length ? { attachments } : {}),
        },
      },
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

function parseStreamEvent(data: string): ArchHypoAgUiEvent {
  const value: unknown = JSON.parse(data);
  if (!value || typeof value !== "object" || !("type" in value) ||
    typeof value.type !== "string") {
    throw new Error("Invalid AG-UI event envelope");
  }
  return value as ArchHypoAgUiEvent;
}
