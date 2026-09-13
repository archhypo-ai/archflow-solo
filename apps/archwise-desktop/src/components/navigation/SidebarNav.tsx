import type { ReactNode } from "react";
import { SidebarNavItem } from "./SidebarNavItem";

export type SidebarNavEntry = {
  id: string;
  label: string;
  icon: ReactNode;
  active?: boolean;
  disabled?: boolean;
  onClick?: () => void;
};

type SidebarNavProps = {
  items: readonly SidebarNavEntry[];
  ariaLabel?: string;
};

export function SidebarNav({
  items,
  ariaLabel = "Sections",
}: SidebarNavProps) {
  return (
    <nav className="sidebar-nav" aria-label={ariaLabel}>
      {items.map((item) => (
        <SidebarNavItem
          key={item.id}
          active={item.active}
          disabled={item.disabled}
          icon={item.icon}
          label={item.label}
          onClick={item.onClick}
        />
      ))}
    </nav>
  );
}
