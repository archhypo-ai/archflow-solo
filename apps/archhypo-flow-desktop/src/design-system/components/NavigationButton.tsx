import type { ButtonHTMLAttributes, ReactNode } from "react";
import "./NavigationButton.css";

type NavigationButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> & {
  icon: ReactNode;
  label: string;
  selected?: boolean;
  iconOnly?: boolean;
};

export function NavigationButton({
  icon, label, selected, iconOnly, className, ...props
}: NavigationButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={selected}
      title={label}
      className={`ds-navigation-button${iconOnly ? " ds-navigation-button--icon-only" : ""}${className ? ` ${className}` : ""}`}
      {...props}
    >
      <span className="ds-navigation-icon" aria-hidden="true">{icon}</span>
      {!iconOnly && <span className="ds-navigation-label">{label}</span>}
    </button>
  );
}
