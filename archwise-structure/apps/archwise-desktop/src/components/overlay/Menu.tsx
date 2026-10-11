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
}>;

export function MenuContent({
  open,
  className = "",
  children,
}: MenuContentProps) {
  if (!open) return null;
  return (
    <div className={`menu-content ${className}`} role="menu">
      {children}
    </div>
  );
}

type MenuItemProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "children"
> & {
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
