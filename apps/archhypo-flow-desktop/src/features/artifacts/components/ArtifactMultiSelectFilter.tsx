import { ChevronDown } from "lucide-react";
import { Menu, MenuCheckboxItem, MenuContent } from "../../../components/overlay";

export type ArtifactFilterOption = {
  value: string;
  label: string;
};

type ArtifactMultiSelectFilterProps = {
  label: string;
  options: ArtifactFilterOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectAllLabel: string;
  clearLabel: string;
  emptyLabel: string;
};

export function ArtifactMultiSelectFilter({
  label,
  options,
  selectedValues,
  onChange,
  open,
  onOpenChange,
  selectAllLabel,
  clearLabel,
  emptyLabel,
}: ArtifactMultiSelectFilterProps) {
  const selected = new Set(selectedValues);

  const toggleValue = (value: string) => {
    onChange(
      selected.has(value)
        ? selectedValues.filter((item) => item !== value)
        : [...selectedValues, value],
    );
  };

  return (
    <Menu
      open={open}
      onOpenChange={onOpenChange}
      className={`artifact-filter-menu${open ? " is-open" : ""}`}
    >
      <button
        className="artifact-filter-trigger"
        type="button"
        aria-label={label}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => onOpenChange(!open)}
      >
        <span>{label}</span>
        {selectedValues.length > 0 && (
          <span className="artifact-filter-selection-count">
            {selectedValues.length}
          </span>
        )}
        <ChevronDown size={15} aria-hidden="true" />
      </button>
      <MenuContent
        open={open}
        className="artifact-filter-menu-content"
        ariaLabel={label}
      >
        <div className="artifact-filter-menu-actions">
          <button
            type="button"
            role="menuitem"
            onClick={() => onChange(options.map((option) => option.value))}
          >
            {selectAllLabel}
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => onChange([])}
          >
            {clearLabel}
          </button>
        </div>
        <div className="artifact-filter-options" role="group">
          {options.length > 0 ? (
            options.map((option) => (
              <MenuCheckboxItem
                checked={selected.has(option.value)}
                key={option.value}
                label={option.label}
                onClick={() => toggleValue(option.value)}
              />
            ))
          ) : (
            <p className="artifact-filter-empty-options">{emptyLabel}</p>
          )}
        </div>
      </MenuContent>
    </Menu>
  );
}
