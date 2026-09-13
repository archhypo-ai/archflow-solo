import {
  ChevronDown,
  Clock3,
  LogOut,
  MessageSquare,
  PanelLeft,
  Pin,
  Plus,
  Settings,
} from "lucide-react";
import { useI18n } from "../../i18n";
import type { Conversation } from "../../features/conversations";
import { Menu, MenuContent, MenuItem } from "../overlay";
import { IconButton } from "../ui/IconButton";
import { useSidebarAccountMenu } from "./hooks/useSidebarAccountMenu";
import { SidebarNav, type SidebarNavEntry } from "./SidebarNav";
import { SidebarSection } from "./SidebarSection";

export type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
  onNewConversation: () => void;
  onSettingsOpen: () => void;
  conversations: readonly Conversation[];
  activeConversationId?: string;
  onConversationSelect: (conversation: Conversation) => void;
  onConversationPinToggle: (conversation: Conversation) => void;
  onConversationDelete: (conversation: Conversation) => void;
};

export function Sidebar({
  collapsed,
  onToggle,
  onNewConversation,
  onSettingsOpen,
  conversations,
  activeConversationId,
  onConversationSelect,
  onConversationPinToggle,
  onConversationDelete,
}: SidebarProps) {
  const { t } = useI18n();
  const accountMenu = useSidebarAccountMenu();
  const navigationItems: readonly SidebarNavEntry[] = [
    {
      id: "chat",
      label: t("app.chat"),
      icon: <MessageSquare aria-hidden="true" />,
      active: true,
    },
  ];
  const recentConversations = conversations.filter((item) => !item.pinned);
  const pinnedConversations = conversations.filter((item) => item.pinned);

  return (
    <aside
      className={`sidebar${collapsed ? " is-collapsed" : ""}`}
      aria-label={t("app.mainNavigation")}
    >
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <strong>ArchWISE</strong>
          <span>{t("app.brandTagline")}</span>
        </div>
        <IconButton
          className="sidebar-toggle"
          label={collapsed ? t("app.showSidebar") : t("app.hideSidebar")}
          onClick={onToggle}
        >
          <PanelLeft aria-hidden="true" />
        </IconButton>
      </div>

      <button
        className="sidebar-new-chat"
        onClick={onNewConversation}
        title={t("app.newConversationTitle")}
        type="button"
      >
        <Plus aria-hidden="true" />
        <span>{t("app.newConversation")}</span>
      </button>

      <SidebarNav ariaLabel={t("app.sections")} items={navigationItems} />

      <div className="sidebar-sections">
        <SidebarSection
          icon={<Clock3 aria-hidden="true" />}
          label={t("app.recent")}
          items={recentConversations}
          activeItemId={activeConversationId}
          emptyLabel={t("app.noConversations")}
          onItemSelect={onConversationSelect}
          onItemPinToggle={onConversationPinToggle}
          onItemDelete={onConversationDelete}
        />
        <SidebarSection
          icon={<Pin aria-hidden="true" />}
          label={t("app.pinned")}
          items={pinnedConversations}
          activeItemId={activeConversationId}
          emptyLabel={t("app.noConversations")}
          onItemSelect={onConversationSelect}
          onItemPinToggle={onConversationPinToggle}
          onItemDelete={onConversationDelete}
        />
      </div>

      <Menu
        className="sidebar-user"
        open={accountMenu.open}
        onOpenChange={accountMenu.setMenuOpen}
      >
        <MenuContent open={accountMenu.open} className="sidebar-user-menu">
          <MenuItem
            icon={<Settings aria-hidden="true" />}
            label={t("app.settings")}
            onClick={() => {
              accountMenu.close();
              onSettingsOpen();
            }}
          />
          <MenuItem
            icon={<LogOut aria-hidden="true" />}
            label={t("app.logout")}
            onClick={accountMenu.close}
          />
        </MenuContent>
        <button
          className="sidebar-user-trigger"
          aria-expanded={accountMenu.open}
          aria-haspopup="menu"
          onClick={accountMenu.toggle}
          title={t("app.account")}
          type="button"
        >
          <span className="user-avatar" aria-hidden="true">
            A
          </span>
          <span className="sidebar-user-name">{t("app.anonymous")}</span>
          <ChevronDown
            className={`sidebar-chevron${accountMenu.open ? " is-open" : ""}`}
            aria-hidden="true"
          />
        </button>
      </Menu>
    </aside>
  );
}
