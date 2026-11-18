import "./Menu.css";
import { IconCheck as Check } from "@tabler/icons-react";
import {
  useEffect,
  useRef,
  type ButtonHTMLAttributes,
  type PropsWithChildren,
  type ReactNode,
} from "react";

type MenuProps = PropsWithChildren<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
  className?: string;
}>;

export function Menu({
  open,
  onOpenChange,
  className = "",
  children,
}: MenuProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) onOpenChange(false);
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onOpenChange, open]);

  return (
    <div ref={rootRef} className={`menu-root ${className}`}>
      {children}
    </div>
  );
}

type MenuContentProps = PropsWithChildren<{
  open: boolean;
  className?: string;
  ariaLabel?: string;
}>;

export function MenuContent({
  open,
  className = "",
  ariaLabel,
  children,
}: MenuContentProps) {
  if (!open) return null;
  return (
    <div className={`menu-content ${className}`} role="menu" aria-label={ariaLabel}>
      {children}
    </div>
  );
}

type MenuItemProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> & {
  icon?: ReactNode;
  label: string;
};

export function MenuItem({
  icon,
  label,
  className = "",
  type = "button",
  ...props
}: MenuItemProps) {
  return (
    <button
      {...props}
      className={`menu-item ${className}`}
      role="menuitem"
      type={type}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

type MenuRadioItemProps = {
  checked: boolean;
  label: string;
  icon?: ReactNode;
  onClick: () => void;
};

export function MenuRadioItem({ checked, label, icon, onClick }: MenuRadioItemProps) {
  return (
    <button
      className="menu-item menu-radio-item"
      type="button"
      role="menuitemradio"
      aria-checked={checked}
      onClick={onClick}
    >
      {icon}
      <span>{label}</span>
      <span className="menu-radio-indicator" aria-hidden="true">
        {checked && <Check size={15} />}
      </span>
    </button>
  );
}

type MenuCheckboxItemProps = {
  checked: boolean;
  label: string;
  onClick: () => void;
};

export function MenuCheckboxItem({
  checked,
  label,
  onClick,
}: MenuCheckboxItemProps) {
  return (
    <button
      className="menu-item menu-checkbox-item"
      type="button"
      role="menuitemcheckbox"
      aria-checked={checked}
      onClick={onClick}
    >
      <span>{label}</span>
      <span className="menu-checkbox-indicator" aria-hidden="true">
        {checked && <Check size={14} />}
      </span>
    </button>
  );
}
