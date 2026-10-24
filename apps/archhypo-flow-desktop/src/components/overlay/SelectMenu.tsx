import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { Menu, MenuContent, MenuRadioItem } from "./Menu";

type SelectMenuOption<Value extends string> = {
  value: Value;
  label: string;
};

type SelectMenuProps<Value extends string> = {
  value: Value;
  options: readonly SelectMenuOption<Value>[];
  onChange: (value: Value) => void;
  label: string;
  disabled?: boolean;
};

export function SelectMenu<Value extends string>({
  value,
  options,
  onChange,
  label,
  disabled = false,
}: SelectMenuProps<Value>) {
  const [open, setOpen] = useState(false);
  const selectedOption = options.find((option) => option.value === value);

  return (
    <Menu
      open={open}
      onOpenChange={setOpen}
      className={`settings-select-menu${open ? " is-open" : ""}`}
    >
      <button
        className="settings-select-trigger"
        type="button"
        disabled={disabled}
        aria-label={label}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((current) => !current)}
      >
        <span>{selectedOption?.label ?? value}</span>
        <ChevronDown size={15} aria-hidden="true" />
      </button>
      <MenuContent
        open={open}
        className="settings-select-content"
        ariaLabel={label}
      >
        {options.map((option) => (
          <MenuRadioItem
            key={option.value}
            checked={option.value === value}
            label={option.label}
            onClick={() => {
              onChange(option.value);
              setOpen(false);
            }}
          />
        ))}
      </MenuContent>
    </Menu>
  );
}
