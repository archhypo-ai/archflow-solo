import {
  ChevronDown,
  MoreHorizontal,
  Pin,
  Trash2,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { useI18n } from "../../i18n";
import type { Conversation } from "../../features/conversations";
import { ConfirmDialog } from "../overlay/ConfirmDialog";
import { Menu, MenuContent, MenuItem } from "../overlay/Menu";

export type SidebarSectionProps = {
  label: string;
  icon: ReactNode;
  items: readonly Conversation[];
  activeItemId?: string;
  emptyLabel: string;
  onItemSelect: (item: Conversation) => void;
  onItemPinToggle: (item: Conversation) => void;
  onItemDelete: (item: Conversation) => void;
};

export function SidebarSection({
  label,
  icon,
  items,
  activeItemId,
  emptyLabel,
  onItemSelect,
  onItemPinToggle,
  onItemDelete,
}: SidebarSectionProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState(true);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [deleteItem, setDeleteItem] = useState<Conversation | null>(null);

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
              <div
                className={`sidebar-conversation-row${
                  item.id === activeItemId ? " is-active" : ""
                }`}
                key={item.id}
              >
                <button
                  className="sidebar-conversation"
                  onClick={() => onItemSelect(item)}
                  title={item.label}
                  type="button"
                >
                  <span>{item.label}</span>
                </button>
                <Menu
                  className="sidebar-conversation-menu"
                  open={openMenuId === item.id}
                  onOpenChange={(menuOpen) =>
                    setOpenMenuId(menuOpen ? item.id : null)
                  }
                >
                  <button
                    className="sidebar-conversation-menu-trigger"
                    aria-label={t("app.conversationOptions")}
                    aria-expanded={openMenuId === item.id}
                    aria-haspopup="menu"
                    onClick={() =>
                      setOpenMenuId((current) =>
                        current === item.id ? null : item.id,
                      )
                    }
                    title={t("app.options")}
                    type="button"
                  >
                    <MoreHorizontal aria-hidden="true" />
                  </button>
                  <MenuContent
                    open={openMenuId === item.id}
                    className="sidebar-conversation-menu-content"
                  >
                    <MenuItem
                      icon={<Pin aria-hidden="true" />}
                      label={item.pinned ? t("app.unpin") : t("app.pin")}
                      onClick={() => {
                        onItemPinToggle(item);
                        setOpenMenuId(null);
                      }}
                    />
                    <MenuItem
                      className="menu-item-danger"
                      icon={<Trash2 aria-hidden="true" />}
                      label={t("app.delete")}
                      onClick={() => {
                        setDeleteItem(item);
                        setOpenMenuId(null);
                      }}
                    />
                  </MenuContent>
                </Menu>
              </div>
            ))}
          </div>
        ) : (
          <p className="sidebar-empty">{emptyLabel}</p>
        ))}
      {deleteItem && (
        <ConfirmDialog
          open
          title={t("app.deleteConversationTitle")}
          description={t("app.deleteConversationDescription", {
            title: deleteItem.label,
          })}
          confirmLabel={t("app.delete")}
          cancelLabel={t("app.cancel")}
          icon={<Trash2 />}
          onCancel={() => setDeleteItem(null)}
          onConfirm={() => {
            onItemDelete(deleteItem);
            setDeleteItem(null);
          }}
        />
      )}
    </section>
  );
}
