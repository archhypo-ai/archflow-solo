import {
  BookOpen,
  Boxes,
  Briefcase,
  Cloud,
  Code,
  Cpu,
  Database,
  FileText,
  Folder,
  FolderOpen,
  GitBranch,
  GitMerge,
  GitPullRequest,
  Globe,
  HardDrive,
  KeyRound,
  Layers,
  LayoutDashboard,
  Lightbulb,
  LockKeyhole,
  Network,
  Package,
  Puzzle,
  Rocket,
  Server,
  Shield,
  Store,
  Terminal,
  Waypoints,
  Wrench,
  Zap,
  Workflow,
  type LucideIcon,
} from "lucide-react";

export type ProjectIconDefinition = {
  id: string;
  Icon: LucideIcon;
};

export const PROJECT_ICONS = [
  { id: "folder", Icon: Folder },
  { id: "folder-open", Icon: FolderOpen },
  { id: "briefcase", Icon: Briefcase },
  { id: "layers", Icon: Layers },
  { id: "dashboard", Icon: LayoutDashboard },
  { id: "package", Icon: Package },
  { id: "boxes", Icon: Boxes },
  { id: "workflow", Icon: Workflow },
  { id: "network", Icon: Network },
  { id: "server", Icon: Server },
  { id: "database", Icon: Database },
  { id: "hard-drive", Icon: HardDrive },
  { id: "cloud", Icon: Cloud },
  { id: "code", Icon: Code },
  { id: "terminal", Icon: Terminal },
  { id: "git-branch", Icon: GitBranch },
  { id: "git-merge", Icon: GitMerge },
  { id: "git-pull-request", Icon: GitPullRequest },
  { id: "shield", Icon: Shield },
  { id: "lock", Icon: LockKeyhole },
  { id: "key", Icon: KeyRound },
  { id: "rocket", Icon: Rocket },
  { id: "zap", Icon: Zap },
  { id: "lightbulb", Icon: Lightbulb },
  { id: "book", Icon: BookOpen },
  { id: "file-text", Icon: FileText },
  { id: "globe", Icon: Globe },
  { id: "store", Icon: Store },
  { id: "waypoints", Icon: Waypoints },
  { id: "puzzle", Icon: Puzzle },
  { id: "wrench", Icon: Wrench },
  { id: "cpu", Icon: Cpu },
] as const satisfies readonly ProjectIconDefinition[];

export type ProjectIconId = (typeof PROJECT_ICONS)[number]["id"];

const projectIconsById: Map<string, LucideIcon> = new Map(
  PROJECT_ICONS.map(({ id, Icon }) => [id, Icon]),
);

export function getProjectIcon(id: ProjectIconId): LucideIcon {
  return projectIconsById.get(id) ?? PROJECT_ICONS[0].Icon;
}

export function isProjectIconId(value: unknown): value is ProjectIconId {
  return typeof value === "string" && projectIconsById.has(value);
}
