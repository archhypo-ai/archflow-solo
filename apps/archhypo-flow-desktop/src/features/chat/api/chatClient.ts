import { HttpAgent, type AbstractAgent } from "@ag-ui/client";
import { getGlobalContext, getHitlEnabled } from "../../settings";
import type {
  HypothesisReviewDecision,
  TechnicalPlanReviewDecision,
} from "../types";

import type { ArchHypoAgUiEvent } from "./agUiEvents";

export const archHypoAgent = new HttpAgent({
  agentId: "archhypo",
  url: "http://127.0.0.1:8765/api/chat/stream",
});

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
  registeredAgent: AbstractAgent = archHypoAgent,
): AsyncGenerator<ArchHypoAgUiEvent> {
  const decision = hypothesisReview ?? technicalPlanReview;
  if (decision && (typeof interruptId !== "string" || !interruptId)) {
    throw new Error("Missing review interrupt ID. Reload the conversation and retry.");
  }
  const global_context = await getGlobalContext();
  if (signal.aborted) return;
  const agent = registeredAgent.clone();
  const queue: ArchHypoAgUiEvent[] = [];
  let closed = false;
  let failure: unknown;
  let wake: (() => void) | undefined;
  const finish = () => { closed = true; wake?.(); };
  const stop = () => { agent.abortRun(); finish(); };
  const subscription = agent.run({
      threadId,
      runId: crypto.randomUUID(),
      messages: message ? [{ id: crypto.randomUUID(), role: "user", content: message }] : [],
      state: {},
      tools: [],
      context: [],
      ...(decision ? { resume: [{
        interruptId: interruptId as string,
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
  }).subscribe({
    next(event: unknown) { queue.push(event as ArchHypoAgUiEvent); wake?.(); },
    error(error: unknown) { failure = error; finish(); },
    complete: finish,
  });
  signal.addEventListener("abort", stop, { once: true });
  try {
    while (!signal.aborted) {
      const event = queue.shift();
      if (event) yield event;
      else if (closed) {
        if (failure) throw failure;
        return;
      } else await new Promise<void>((resolve) => { wake = resolve; });
    }
  } finally {
    signal.removeEventListener("abort", stop);
    subscription.unsubscribe();
    if (!closed) stop();
  }
}
