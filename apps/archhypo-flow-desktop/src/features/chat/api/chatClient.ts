import type { ChatTurnResponse } from "../types";

const API_BASE_URL = "http://127.0.0.1:8765";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
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

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function sendChatMessage(
  threadId: string,
  message: string,
  language: "en" | "pt-BR",
  projectId: string | null,
): Promise<ChatTurnResponse> {
  return request<ChatTurnResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      thread_id: threadId,
      message,
      language,
      project_id: projectId,
    }),
  });
}
