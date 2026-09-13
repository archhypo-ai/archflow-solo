import {
  Clock3,
  MessageSquare,
  PanelLeft,
  Pin,
  Plus,
} from "lucide-react";
import type { Conversation } from "../../features/conversations";
import { IconButton } from "../ui/IconButton";
import { SidebarSection } from "./SidebarSection";

export type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
  onNewConversation: () => void;
  conversations: readonly Conversation[];
  activeConversationId?: string;
  onConversationSelect: (conversation: Conversation) => void;
};

export function Sidebar({
  collapsed,
  onToggle,
  onNewConversation,
  conversations,
  activeConversationId,
  onConversationSelect,
}: SidebarProps) {
  const recentConversations = conversations.filter((item) => !item.pinned);
  const pinnedConversations = conversations.filter((item) => item.pinned);

  return (
    <aside className={`sidebar${collapsed ? " is-collapsed" : ""}`}>
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <strong>ArchWISE</strong>
          <span>Hypothesis Architecture Agents</span>
        </div>
        <IconButton
          className="sidebar-toggle"
          label={collapsed ? "Show sidebar" : "Hide sidebar"}
          onClick={onToggle}
        >
          <PanelLeft aria-hidden="true" />
        </IconButton>
      </div>

      <button
        className="sidebar-new-chat"
        onClick={onNewConversation}
        title="New conversation"
        type="button"
      >
        <Plus aria-hidden="true" />
        <span>New conversation</span>
      </button>

      <nav className="sidebar-nav" aria-label="Sections">
        <button className="sidebar-nav-item is-active" type="button">
          <MessageSquare aria-hidden="true" />
          <span>Chat</span>
        </button>
      </nav>

      <div className="sidebar-sections">
        <SidebarSection
          icon={<Clock3 aria-hidden="true" />}
          label="Recent"
          items={recentConversations}
          activeItemId={activeConversationId}
          emptyLabel="No recent conversations"
          onItemSelect={onConversationSelect}
        />
        <SidebarSection
          icon={<Pin aria-hidden="true" />}
          label="Pinned"
          items={pinnedConversations}
          activeItemId={activeConversationId}
          emptyLabel="No pinned conversations"
          onItemSelect={onConversationSelect}
        />
      </div>
    </aside>
  );
}
