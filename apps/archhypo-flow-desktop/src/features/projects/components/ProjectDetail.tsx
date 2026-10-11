import {
  MessageSquarePlus,
  MoreHorizontal,
  Pencil,
  PinOff,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../../../i18n";
import { Menu, MenuContent, MenuItem } from "../../../components/overlay";
import type { ConversationSummary } from "../../conversations/types";
import "./ProjectDetail.css";

type ProjectDetailProps = {
  conversations: ConversationSummary[];
  language: AppLanguage;
  onSelectConversation: (threadId: string) => void;
  onRenameConversation: (conversation: ConversationSummary) => void;
  onToggleConversationPin: (conversation: ConversationSummary) => void;
  onDeleteConversation: (conversation: ConversationSummary) => void;
};

export function ProjectDetail({
  conversations,
  language,
  onSelectConversation,
  onRenameConversation,
  onToggleConversationPin,
  onDeleteConversation,
}: ProjectDetailProps) {
  const { t } = useTranslation();
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  return (
    <div className="project-detail">
      <section className="project-chat-section" aria-labelledby="project-chats-heading">
        <h2 id="project-chats-heading">{t("projects.chatsTitle")}</h2>
        {conversations.length === 0 ? (
          <div className="project-empty-state">
            <MessageSquarePlus size={20} aria-hidden="true" />
            <h3>{t("projects.emptyTitle")}</h3>
            <p>{t("projects.emptyDescription")}</p>
          </div>
        ) : (
          <div className="project-chat-list">
            {conversations.map((conversation) => {
              const menuOpen = openMenuId === conversation.threadId;
              return (
                <div className="project-chat-row" key={conversation.threadId}>
                  <button
                    className="project-chat-content"
                    type="button"
                    onClick={() => onSelectConversation(conversation.threadId)}
                    title={conversation.title}
                  >
                    <span className="project-chat-heading">
                      <span className="project-chat-title">{conversation.title}</span>
                      <time
                        className="project-chat-time"
                        dateTime={conversation.updatedAt}
                        title={conversation.updatedAt}
                      >
                        {formatLastActivity(conversation.updatedAt, language)}
                      </time>
                    </span>
                    <span className="project-chat-preview">
                      {conversation.preview || t("projects.noPreview")}
                    </span>
                  </button>
                  <Menu
                    className="project-chat-actions"
                    open={menuOpen}
                    onOpenChange={(open) =>
                      setOpenMenuId(open ? conversation.threadId : null)
                    }
                  >
                    <button
                      className="project-chat-menu-trigger"
                      type="button"
                      aria-label={t("conversations.actions")}
                      aria-haspopup="menu"
                      aria-expanded={menuOpen}
                      onClick={() => setOpenMenuId(menuOpen ? null : conversation.threadId)}
                    >
                      <MoreHorizontal size={16} aria-hidden="true" />
                    </button>
                    <MenuContent
                      open={menuOpen}
                      className="project-chat-menu"
                      ariaLabel={t("conversations.actions")}
                    >
                      <MenuItem
                        icon={<Pencil aria-hidden="true" />}
                        label={t("conversations.rename")}
                        onClick={() => {
                          setOpenMenuId(null);
                          onRenameConversation(conversation);
                        }}
                      />
                      {conversation.pinned && (
                        <MenuItem
                          icon={<PinOff aria-hidden="true" />}
                          label={t("conversations.unpin")}
                          onClick={() => {
                            setOpenMenuId(null);
                            onToggleConversationPin(conversation);
                          }}
                        />
                      )}
                      <MenuItem
                        className="menu-item-danger"
                        icon={<Trash2 aria-hidden="true" />}
                        label={t("conversations.delete")}
                        onClick={() => {
                          setOpenMenuId(null);
                          onDeleteConversation(conversation);
                        }}
                      />
                    </MenuContent>
                  </Menu>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function formatLastActivity(value: string, language: AppLanguage): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  const elapsed = Math.max(0, Date.now() - date.getTime());
  const relative = new Intl.RelativeTimeFormat(language, {
    numeric: "always",
    style: "short",
  });
  if (elapsed < 60 * 60 * 1000) {
    const minutes = Math.max(1, Math.floor(elapsed / (60 * 1000)));
    return relative.format(-minutes, "minute");
  }
  if (elapsed < 24 * 60 * 60 * 1000) {
    const hours = Math.max(1, Math.floor(elapsed / (60 * 60 * 1000)));
    return relative.format(-hours, "hour");
  }
  return new Intl.DateTimeFormat(language, {
    month: "short",
    day: "numeric",
  }).format(date);
}
