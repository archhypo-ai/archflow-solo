import type { PropsWithChildren } from "react";
import type { Conversation } from "../../features/conversations";
import { Sidebar } from "../navigation";
import { useSidebar } from "./hooks/useSidebar";

export type AppShellProps = PropsWithChildren<{
  conversations: readonly Conversation[];
  activeConversationId?: string;
  onNewConversation: () => void;
  onSettingsOpen: () => void;
  onConversationSelect: (conversation: Conversation) => void;
  onConversationPinToggle: (conversation: Conversation) => void;
  onConversationDelete: (conversation: Conversation) => void;
}>;

export function AppShell({
  children,
  conversations,
  activeConversationId,
  onNewConversation,
  onSettingsOpen,
  onConversationSelect,
  onConversationPinToggle,
  onConversationDelete,
}: AppShellProps) {
  const sidebar = useSidebar();

  return (
    <main className={`app-shell${sidebar.collapsed ? " sidebar-collapsed" : ""}`}>
      <Sidebar
        collapsed={sidebar.collapsed}
        onToggle={sidebar.toggle}
        onNewConversation={onNewConversation}
        onSettingsOpen={onSettingsOpen}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onConversationSelect={onConversationSelect}
        onConversationPinToggle={onConversationPinToggle}
        onConversationDelete={onConversationDelete}
      />
      <section className="main-content">{children}</section>
    </main>
  );
}
