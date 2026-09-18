import i18n from "../../../i18n/config";
import type {
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
