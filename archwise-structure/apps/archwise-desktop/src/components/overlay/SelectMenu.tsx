import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";
import { Menu, MenuContent } from "./Menu";

type SelectMenuOption<T extends string> = {
  value: T;
  label: string;
};

type SelectMenuProps<T extends string> = {
  value: T;
  options: readonly SelectMenuOption<T>[];
  onChange: (value: T) => void;
  label: string;
};

export function SelectMenu<T extends string>({
  value,
  options,
  onChange,
  label,
}: SelectMenuProps<T>) {
  const [open, setOpen] = useState(false);
  const selectedOption = options.find((option) => option.value === value);

  return (
    <Menu open={open} onOpenChange={setOpen} className="select-menu">
      <button
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={label}
        className="select-menu-trigger"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span>{selectedOption?.label ?? value}</span>
        <ChevronDown aria-hidden="true" />
      </button>
      <MenuContent open={open} className="select-menu-content">
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <button
              aria-checked={selected}
              className={`select-menu-option${selected ? " is-selected" : ""}`}
              key={option.value}
              onClick={() => {
                onChange(option.value);
                setOpen(false);
              }}
              role="menuitemradio"
              type="button"
            >
              <span>{option.label}</span>
              <span className="select-menu-check" aria-hidden="true">
                {selected && <Check />}
              </span>
            </button>
          );
        })}
      </MenuContent>
    </Menu>
  );
}
