import type { ComponentPropsWithoutRef } from "react";
import "./Switch.css";

type Props = Omit<ComponentPropsWithoutRef<"button">, "children" | "onClick"> & {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
};

export function Switch({ checked, onCheckedChange, className, ...props }: Props) {
  return (
    <button {...props} className={`settings-switch${className ? ` ${className}` : ""}`}
      type="button" role="switch" aria-checked={checked} onClick={() => onCheckedChange(!checked)}>
      <span className="settings-switch-thumb" aria-hidden="true" />
    </button>
  );
}
