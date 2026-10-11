import type { ProjectIconId } from "./projectIcons";

export const PROJECT_COLORS = [
  "neutral",
  "red",
  "orange",
  "yellow",
  "green",
  "blue",
  "purple",
  "pink",
] as const;

export type ProjectColor = (typeof PROJECT_COLORS)[number];

export type Project = {
  id: string;
  name: string;
  icon: ProjectIconId;
  color: ProjectColor;
  instructions: string;
};
