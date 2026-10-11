import type { ButtonHTMLAttributes, ReactNode } from "react";

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  children: ReactNode;
};

export function IconButton({ label, children, ...props }: IconButtonProps) {
  return (
    <button
      {...props}
      className={`icon-button${props.className ? ` ${props.className}` : ""}`}
      aria-label={label}
      title={label}
      type={props.type ?? "button"}
    >
      {children}
    </button>
  );
}
