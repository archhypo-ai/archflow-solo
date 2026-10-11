import { Clock3, MessageSquareText, Moon, Plus, Sparkles, Sun } from "lucide-react";
import "./Sidebar.css";

type Theme = "day" | "night";

type SidebarProps = {
  theme: Theme;
  activeConversationTitle: string;
  onNewChat: () => void;
  onToggleTheme: () => void;
};

export function Sidebar({
  theme,
  activeConversationTitle,
  onNewChat,
  onToggleTheme,
}: SidebarProps) {
  const nextTheme = theme === "night" ? "Day" : "Night";
  const ThemeIcon = theme === "night" ? Sun : Moon;

  return (
    <aside className="sidebar" aria-label="Navegação principal">
      <div className="sidebar-brand">
        <span className="sidebar-brand-mark" aria-hidden="true">
          <Sparkles size={18} />
        </span>
        <span className="sidebar-brand-text">
          <strong>ArchHypo</strong>
          <span>FLOW</span>
        </span>
      </div>

      <button className="sidebar-new-chat" onClick={onNewChat} type="button">
        <Plus size={17} aria-hidden="true" />
        <span>Nova conversa</span>
      </button>

      <nav className="sidebar-navigation" aria-label="Seções">
        <button className="sidebar-nav-item is-active" type="button">
          <MessageSquareText size={17} aria-hidden="true" />
          <span>Chat</span>
        </button>
      </nav>

      <section className="sidebar-recent" aria-labelledby="recent-title">
        <div className="sidebar-section-heading">
          <Clock3 size={14} aria-hidden="true" />
          <h2 id="recent-title">Conversas recentes</h2>
        </div>
        {activeConversationTitle ? (
          <div className="sidebar-conversation is-active" title={activeConversationTitle}>
            <MessageSquareText size={14} aria-hidden="true" />
            <span>{activeConversationTitle}</span>
          </div>
        ) : (
          <p className="sidebar-empty">As conversas aparecerão aqui.</p>
        )}
      </section>

      <div className="sidebar-footer">
        <button
          className="sidebar-theme-toggle"
          onClick={onToggleTheme}
          type="button"
          aria-label={`Alternar para Tokyo ${nextTheme}`}
          title={`Alternar para Tokyo ${nextTheme}`}
        >
          <ThemeIcon size={17} aria-hidden="true" />
          <span>Tokyo {nextTheme}</span>
        </button>
        <div className="sidebar-profile">
          <span className="sidebar-profile-mark" aria-hidden="true">A</span>
          <span className="sidebar-profile-text">
            <strong>ArchHypo Flow</strong>
          </span>
        </div>
      </div>
    </aside>
  );
}
