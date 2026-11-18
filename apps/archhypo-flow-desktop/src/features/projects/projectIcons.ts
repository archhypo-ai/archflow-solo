import {
  IconBook as BookOpen,
  IconBoxMultiple as Boxes,
  IconBriefcase as Briefcase,
  IconCloud as Cloud,
  IconCode as Code,
  IconCpu as Cpu,
  IconDatabase as Database,
  IconFileText as FileText,
  IconFolder as Folder,
  IconFolderOpen as FolderOpen,
  IconGitBranch as GitBranch,
  IconGitMerge as GitMerge,
  IconGitPullRequest as GitPullRequest,
  IconGlobe as Globe,
  IconDeviceSdCard as HardDrive,
  IconKey as KeyRound,
  IconStack2 as Layers,
  IconLayoutDashboard as LayoutDashboard,
  IconBulb as Lightbulb,
  IconLock as LockKeyhole,
  IconNetwork as Network,
  IconPackage as Package,
  IconPuzzle as Puzzle,
  IconRocket as Rocket,
  IconServer as Server,
  IconShield as Shield,
  IconBuildingStore as Store,
  IconTerminal as Terminal,
  IconTopologyStar as Waypoints,
  IconTool as Wrench,
  IconBolt as Zap,
  IconSitemap as Workflow,
  type Icon,
} from "@tabler/icons-react";

export type ProjectIconDefinition = {
  id: string;
  Icon: Icon;
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

const projectIconsById: Map<string, Icon> = new Map(
  PROJECT_ICONS.map(({ id, Icon }) => [id, Icon]),
);

export function getProjectIcon(id: ProjectIconId): Icon {
  return projectIconsById.get(id) ?? PROJECT_ICONS[0].Icon;
}

export function isProjectIconId(value: unknown): value is ProjectIconId {
  return typeof value === "string" && projectIconsById.has(value);
}
