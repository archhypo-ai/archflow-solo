import { getProjectIcon, type ProjectIconId } from "../projectIcons";
import type { ProjectColor } from "../types";

type ProjectIconProps = {
  icon: ProjectIconId;
  color: ProjectColor;
  size?: number;
  className?: string;
};

export function ProjectIcon({
  icon,
  color,
  size = 16,
  className,
}: ProjectIconProps) {
  const Icon = getProjectIcon(icon);
  return (
    <Icon
      className={className}
      size={size}
      strokeWidth={1.8}
      style={{ color: `var(--project-color-${color})` }}
      aria-hidden="true"
    />
  );
}
