import type {
  ChatTurnResponse,
  ConversationSummary,
  StoredChatMessage,
  StoredConversation,
} from "../types";

const API_BASE_URL = "http://127.0.0.1:8765";

type BackendConversationSummary = {
  thread_id: string;
  title: string;
  message_count: number;
  updated_at: string;
  pinned: boolean;
};

type BackendConversation = BackendConversationSummary & {
  messages: StoredChatMessage[];
};

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
      // Keep the HTTP status text when the error body is not JSON.
    }
    throw new Error(`Chat API error (${response.status}): ${detail}`);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function toConversation(summary: BackendConversationSummary): ConversationSummary {
  return {
    threadId: summary.thread_id,
    title: summary.title,
    messageCount: summary.message_count,
    updatedAt: summary.updated_at,
    pinned: summary.pinned,
  };
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const summaries = await request<BackendConversationSummary[]>("/api/threads");
  return summaries.map(toConversation);
}

export async function getConversation(
  threadId: string,
): Promise<StoredConversation | null> {
  const response = await fetch(
    `${API_BASE_URL}/api/threads/${encodeURIComponent(threadId)}`,
  );
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error(`Chat API error (${response.status}): ${response.statusText}`);
  }
  const conversation = (await response.json()) as BackendConversation;
  return {
    ...toConversation(conversation),
    messages: conversation.messages,
  };
}

export async function updateConversation(
  threadId: string,
  update: { title?: string; pinned?: boolean },
): Promise<ConversationSummary> {
  const summary = await request<BackendConversationSummary>(
    `/api/threads/${encodeURIComponent(threadId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ title: update.title, pinned: update.pinned }),
    },
  );
  return toConversation(summary);
}

export function deleteConversation(threadId: string): Promise<void> {
  return request<void>(`/api/threads/${encodeURIComponent(threadId)}`, {
    method: "DELETE",
  });
}

export function sendChatMessage(
  threadId: string,
  message: string,
  language: "en" | "pt-BR",
): Promise<ChatTurnResponse> {
  return request<ChatTurnResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ thread_id: threadId, message, language }),
  });
}
