import { PROJECT_COLORS, type Project } from "./types";
import { isProjectIconId } from "./projectIcons";

const PROJECTS_STORAGE_KEY = "archhypo-flow-projects";
const projectColors = new Set<string>(PROJECT_COLORS);

function isProject(value: unknown): value is Project {
  if (!value || typeof value !== "object") return false;

  const project = value as Record<string, unknown>;
  return (
    typeof project.id === "string" &&
    typeof project.name === "string" &&
    isProjectIconId(project.icon) &&
    typeof project.color === "string" &&
    projectColors.has(project.color) &&
    typeof project.instructions === "string"
  );
}

export function loadProjects(): Project[] {
  try {
    const stored = localStorage.getItem(PROJECTS_STORAGE_KEY);
    if (!stored) return [];

    const parsed: unknown = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed.filter(isProject) : [];
  } catch {
    return [];
  }
}

export function saveProjects(projects: Project[]): void {
  try {
    localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
  } catch {
    // Project persistence is best-effort when browser storage is unavailable.
  }
}
