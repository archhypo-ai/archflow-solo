import i18n from "../../../i18n/config";
import type {
  AgentStreamEvent,
  BackendActiveRun,
  BackendChatResponse,
  BackendFolderContext,
  BackendThread,
  BackendThreadSummary,
} from "../types";

const API_URL =
  import.meta.env.VITE_ARCHWISE_API_URL ?? "http://127.0.0.1:8765";

type ErrorResponse = {
  detail?: string;
};

async function requestError(response: Response): Promise<Error> {
  let detail = i18n.t("chat.communicationError");
  try {
    const payload = (await response.json()) as ErrorResponse;
    if (payload.detail) detail = payload.detail;
  } catch {
    // Keep the generic message when the API does not return JSON.
  }
  return new Error(detail);
}

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(i18n.t("chat.communicationError"));
  }

  if (!response.ok) throw await requestError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function getActiveRun(
  threadId: string,
  signal?: AbortSignal,
): Promise<BackendActiveRun | null> {
  return request<BackendActiveRun | null>(
    `${API_URL}/api/threads/${encodeURIComponent(threadId)}/runs/active`,
    { signal },
  );
}

export async function listThreads(): Promise<BackendThreadSummary[]> {
  return request<BackendThreadSummary[]>(`${API_URL}/api/threads`);
}

export async function getThread(
  threadId: string,
  signal?: AbortSignal,
): Promise<BackendThread | null> {
  const response = await fetch(
    `${API_URL}/api/threads/${encodeURIComponent(threadId)}`,
    { signal },
  ).catch((error: unknown) => {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(i18n.t("chat.communicationError"));
  });

  if (response.status === 404) return null;
  if (!response.ok) throw await requestError(response);
  return (await response.json()) as BackendThread;
}

export async function sendChatMessage(
  threadId: string,
  message: string,
  signal?: AbortSignal,
  runId?: string,
): Promise<BackendChatResponse> {
  return request<BackendChatResponse>(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      thread_id: threadId,
      message,
      run_id: runId,
      workspace_id: "default",
      project_id: null,
      user_id: null,
    }),
    signal,
  });
}

/**
 * Execute a turn over SSE so tool-call parts can be rendered while the agent
 * runs. The regular request/response endpoint remains available to non-chat
 * clients.
 */
export async function streamChatMessage(
  threadId: string,
  message: string,
  signal: AbortSignal | undefined,
  runId: string | undefined,
  onEvent: (event: AgentStreamEvent) => void,
): Promise<BackendChatResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/chat/stream`, {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        thread_id: threadId,
        message,
        run_id: runId,
        workspace_id: "default",
        project_id: null,
        user_id: null,
      }),
      signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(i18n.t("chat.communicationError"));
  }

  if (!response.ok) throw await requestError(response);
  if (!response.body) throw new Error(i18n.t("chat.communicationError"));

  let text = "";
  let completed = false;
  let cancelled = false;
  for await (const event of readAgentEvents(response.body, signal)) {
    onEvent(event);
    if (event.type === "text_delta") text += event.text;
    if (event.type === "done") completed = true;
    if (event.type === "cancelled") cancelled = true;
    if (event.type === "error") throw new Error(event.message);
  }

  if (!completed && !cancelled) {
    throw new Error(i18n.t("chat.executionError"));
  }
  return { thread_id: threadId, message: text, status: "completed" };
}

async function* readAgentEvents(
  body: ReadableStream<Uint8Array>,
  signal?: AbortSignal,
): AsyncGenerator<AgentStreamEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let dataLines: string[] = [];

  const emit = (): AgentStreamEvent | undefined => {
    if (dataLines.length === 0) return undefined;
    const data = dataLines.join("\n");
    dataLines = [];
    return parseAgentEvent(data);
  };

  while (true) {
    if (signal?.aborted) return;
    const chunk = await reader.read();
    buffer += decoder.decode(chunk.value ?? new Uint8Array(), {
      stream: !chunk.done,
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

    if (chunk.done) {
      if (buffer.startsWith("data:")) {
        dataLines.push(buffer.slice(5).replace(/^ /, ""));
      }
      const event = emit();
      if (event) yield event;
      return;
    }
  }
}

function parseAgentEvent(data: string): AgentStreamEvent {
  let value: unknown;
  try {
    value = JSON.parse(data);
  } catch {
    throw new Error(i18n.t("chat.executionError"));
  }

  if (!isRecord(value) || value.protocol_version !== 1) {
    throw new Error(i18n.t("chat.executionError"));
  }
  if (
    typeof value.run_id !== "string" ||
    typeof value.thread_id !== "string" ||
    typeof value.type !== "string"
  ) {
    throw new Error(i18n.t("chat.executionError"));
  }

  switch (value.type) {
    case "phase":
      return requireEventFields(value, ["phase"]);
    case "text_delta":
      return requireEventFields(value, ["text"]);
    case "done":
      return requireEventFields(value, ["status"]);
    case "cancelled":
      return value as unknown as AgentStreamEvent;
    case "error":
      return requireEventFields(value, ["message"]);
    case "tool_call_start":
      return requireEventFields(value, ["tool_call_id", "name"]);
    case "tool_call_delta":
      return requireEventFields(value, ["tool_call_id", "text"]);
    case "tool_result":
      return requireEventFields(value, ["tool_call_id", "output"]);
    case "interrupt":
      return requireEventFields(value, ["interrupt_id", "message"]);
    default:
      throw new Error(i18n.t("chat.executionError"));
  }
}

function requireEventFields(
  value: Record<string, unknown>,
  fields: string[],
): AgentStreamEvent {
  if (fields.some((field) => !(field in value))) {
    throw new Error(i18n.t("chat.executionError"));
  }
  return value as unknown as AgentStreamEvent;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export async function attachFolderContext(
  threadId: string,
  folderName: string,
  files: File[],
  signal?: AbortSignal,
): Promise<BackendFolderContext> {
  const formData = new FormData();
  formData.append("folder_name", folderName);
  for (const file of files) {
    formData.append("files", file, file.webkitRelativePath || file.name);
  }

  return request<BackendFolderContext>(
    `${API_URL}/api/threads/${encodeURIComponent(threadId)}/folder-context`,
    {
      method: "POST",
      body: formData,
      signal,
    },
  );
}

export async function attachFolderPath(
  threadId: string,
  folderPath: string,
  signal?: AbortSignal,
): Promise<BackendFolderContext> {
  return request<BackendFolderContext>(
    `${API_URL}/api/threads/${encodeURIComponent(threadId)}/folder-context/path`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder_path: folderPath }),
      signal,
    },
  );
}

export async function deleteFolderContext(threadId: string): Promise<void> {
  await request<void>(
    `${API_URL}/api/threads/${encodeURIComponent(threadId)}/folder-context`,
    { method: "DELETE" },
  );
}

export async function cancelChatRun(runId: string): Promise<boolean> {
  const response = await request<{ run_id: string; cancelled: boolean }>(
    `${API_URL}/api/chat/runs/${encodeURIComponent(runId)}/cancel`,
    { method: "POST" },
  );
  return response.cancelled;
}

export async function updateThread(
  threadId: string,
  update: { pinned?: boolean; title?: string },
): Promise<BackendThreadSummary> {
  return request<BackendThreadSummary>(
    `${API_URL}/api/threads/${encodeURIComponent(threadId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    },
  );
}

export async function deleteThread(threadId: string): Promise<void> {
  await request<void>(`${API_URL}/api/threads/${encodeURIComponent(threadId)}`, {
    method: "DELETE",
  });
}
