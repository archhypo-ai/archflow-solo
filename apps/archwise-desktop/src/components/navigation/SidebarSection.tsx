import { ChevronDown } from "lucide-react";
import { useState, type ReactNode } from "react";
import type { Conversation } from "../../features/conversations";

export type SidebarSectionProps = {
  label: string;
  icon: ReactNode;
  items: readonly Conversation[];
  activeItemId?: string;
  emptyLabel: string;
  onItemSelect: (item: Conversation) => void;
};

export function SidebarSection({
  label,
  icon,
  items,
  activeItemId,
  emptyLabel,
  onItemSelect,
}: SidebarSectionProps) {
  const [open, setOpen] = useState(true);

  return (
    <section className="sidebar-section">
      <button
        className="sidebar-section-toggle"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        {icon}
        <span className="sidebar-section-title">{label}</span>
        <ChevronDown
          className={`sidebar-chevron${open ? " is-open" : ""}`}
          aria-hidden="true"
        />
      </button>
      {open &&
        (items.length > 0 ? (
          <div className="sidebar-section-items">
            {items.map((item) => (
              <button
                className={`sidebar-conversation${
                  item.id === activeItemId ? " is-active" : ""
                }`}
                key={item.id}
                onClick={() => onItemSelect(item)}
                title={item.label}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
        ) : (
          <p className="sidebar-empty">{emptyLabel}</p>
        ))}
    </section>
  );
}
