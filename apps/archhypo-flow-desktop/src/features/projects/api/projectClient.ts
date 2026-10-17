import type { Project } from "../types";

const API_BASE_URL = "http://127.0.0.1:8765";

type BackendProject = Project & {
  created_at: string;
  updated_at: string;
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
      // Keep the HTTP status text if the error body is not JSON.
    }
    throw new Error(`Project API error (${response.status}): ${detail}`);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function toProject(project: BackendProject): Project {
  return {
    id: project.id,
    name: project.name,
    icon: project.icon,
    color: project.color,
    instructions: project.instructions,
  };
}

export async function listProjects(): Promise<Project[]> {
  const projects = await request<BackendProject[]>("/api/projects");
  return projects.map(toProject);
}

export async function createProject(project: Project): Promise<Project> {
  const created = await request<BackendProject>("/api/projects", {
    method: "POST",
    body: JSON.stringify(project),
  });
  return toProject(created);
}

export async function updateProjectSettings(project: Project): Promise<Project> {
  const updated = await request<BackendProject>(
    `/api/projects/${encodeURIComponent(project.id)}`,
    {
      method: "PUT",
      body: JSON.stringify({
        name: project.name,
        icon: project.icon,
        color: project.color,
        instructions: project.instructions,
      }),
    },
  );
  return toProject(updated);
}

export function deleteProject(projectId: string): Promise<void> {
  return request<void>(`/api/projects/${encodeURIComponent(projectId)}`, {
    method: "DELETE",
  });
}
