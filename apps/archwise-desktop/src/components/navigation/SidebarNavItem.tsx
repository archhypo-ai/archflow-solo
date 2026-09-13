import type { ButtonHTMLAttributes, ReactNode } from "react";

type SidebarNavItemProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "children"
> & {
  icon: ReactNode;
  label: string;
  active?: boolean;
};

export function SidebarNavItem({
  icon,
  label,
  active = false,
  className = "",
  type = "button",
  ...props
}: SidebarNavItemProps) {
  return (
    <button
      {...props}
      className={`sidebar-nav-item${active ? " is-active" : ""}${
        className ? ` ${className}` : ""
      }`}
      title={props.title ?? label}
      type={type}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
