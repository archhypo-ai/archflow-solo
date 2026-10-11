import {
  ChevronDown,
  ChevronRight,
  FolderPlus,
  Languages,
  LogOut,
  MoreHorizontal,
  Pencil,
  Pin,
  PinOff,
  Settings2,
  Trash2,
  SquarePen,
} from "lucide-react";
import { useCallback, useEffect, useState, type RefObject } from "react";
import { useTranslation } from "react-i18next";
import type { AppLanguage } from "../i18n";
import { ProjectIcon, type Project } from "../features/projects";
import type { ConversationSummary } from "../features/chat/types";
import { Menu, MenuContent, MenuItem, MenuRadioItem } from "./overlay";
import "./Sidebar.css";

type SidebarProps = {
  accountTriggerRef: RefObject<HTMLButtonElement | null>;
  activeConversationId: string | null;
  isNewConversationActive: boolean;
  conversations: ConversationSummary[];
  language: AppLanguage;
  projects: Project[];
  onConversationSelect: (threadId: string) => void;
  onRenameConversation: (conversation: ConversationSummary) => void;
  onToggleConversationPin: (conversation: ConversationSummary) => void;
  onDeleteConversation: (conversation: ConversationSummary) => void;
  onNewChat: () => void;
  onNewProject: () => void;
  onLanguageChange: (language: AppLanguage) => void;
  onSettingsOpen: () => void;
};

export function Sidebar({
  accountTriggerRef,
  activeConversationId,
  isNewConversationActive,
  conversations,
  language,
  projects,
  onConversationSelect,
  onRenameConversation,
  onToggleConversationPin,
  onDeleteConversation,
  onNewChat,
  onNewProject,
  onLanguageChange,
  onSettingsOpen,
}: SidebarProps) {
  const { t } = useTranslation();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);
  const [projectsExpanded, setProjectsExpanded] = useState(false);
  const [pinsExpanded, setPinsExpanded] = useState(false);
  const [conversationsExpanded, setConversationsExpanded] = useState(false);
  const [openConversationMenuId, setOpenConversationMenuId] = useState<string | null>(null);
  const pinnedConversations = conversations.filter((conversation) => conversation.pinned);
  const unpinnedConversations = conversations.filter((conversation) => !conversation.pinned);

  useEffect(() => {
    if (unpinnedConversations.length > 0) setConversationsExpanded(true);
  }, [unpinnedConversations.length]);
  useEffect(() => {
    if (pinnedConversations.length > 0) setPinsExpanded(true);
  }, [pinnedConversations.length]);
  useEffect(() => {
    if (projects.length > 0) setProjectsExpanded(true);
  }, [projects.length]);

  const renderConversationItems = (items: ConversationSummary[]) => (
    <div className="sidebar-section-items sidebar-conversation-items">
      {items.map((conversation) => {
        const isActive = conversation.threadId === activeConversationId;
        const menuOpen = openConversationMenuId === conversation.threadId;
        return (
          <div
            className={`sidebar-conversation-row${isActive ? " is-active" : ""}`}
            key={conversation.threadId}
          >
            <button
              className="sidebar-conversation"
              type="button"
              title={conversation.title}
              aria-current={isActive ? "page" : undefined}
              onClick={() => onConversationSelect(conversation.threadId)}
            >
              <span>{conversation.title}</span>
            </button>
            <Menu
              className="sidebar-conversation-actions"
              open={menuOpen}
              onOpenChange={(open) =>
                setOpenConversationMenuId(open ? conversation.threadId : null)
              }
            >
              <button
                className="sidebar-conversation-menu-trigger"
                type="button"
                aria-label={t("conversations.actions")}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                onClick={() =>
                  setOpenConversationMenuId(menuOpen ? null : conversation.threadId)
                }
              >
                <MoreHorizontal size={16} aria-hidden="true" />
              </button>
              <MenuContent
                open={menuOpen}
                className="sidebar-conversation-menu"
                ariaLabel={t("conversations.actions")}
              >
                <MenuItem
                  icon={<Pencil aria-hidden="true" />}
                  label={t("conversations.rename")}
                  onClick={() => {
                    setOpenConversationMenuId(null);
                    onRenameConversation(conversation);
                  }}
                />
                <MenuItem
                  icon={conversation.pinned ? <PinOff aria-hidden="true" /> : <Pin aria-hidden="true" />}
                  label={t(conversation.pinned ? "conversations.unpin" : "conversations.pin")}
                  onClick={() => {
                    setOpenConversationMenuId(null);
                    onToggleConversationPin(conversation);
                  }}
                />
                <MenuItem
                  className="menu-item-danger"
                  icon={<Trash2 aria-hidden="true" />}
                  label={t("conversations.delete")}
                  onClick={() => {
                    setOpenConversationMenuId(null);
                    onDeleteConversation(conversation);
                  }}
                />
              </MenuContent>
            </Menu>
          </div>
        );
      })}
    </div>
  );

  const handleMenuOpenChange = useCallback((open: boolean) => {
    setAccountMenuOpen(open);
    if (!open) setLanguageMenuOpen(false);
  }, []);
  const closeAccountMenu = useCallback(() => {
    setAccountMenuOpen(false);
    setLanguageMenuOpen(false);
  }, []);
  const selectLanguage = useCallback(
    (nextLanguage: AppLanguage) => {
      onLanguageChange(nextLanguage);
      closeAccountMenu();
    },
    [closeAccountMenu, onLanguageChange],
  );

  return (
    <aside className="sidebar" aria-label={t("sidebar.navigationLabel")}>
      <div className="sidebar-primary-actions">
        <button
          className={`sidebar-action-button${isNewConversationActive ? " is-active" : ""}`}
          onClick={onNewChat}
          type="button"
          aria-pressed={isNewConversationActive}
        >
          <SquarePen size={17} aria-hidden="true" />
          <span>{t("sidebar.newConversation")}</span>
        </button>
        <button
          className="sidebar-action-button"
          onClick={onNewProject}
          type="button"
        >
          <FolderPlus size={17} aria-hidden="true" />
          <span>{t("sidebar.newProject")}</span>
        </button>
      </div>

      <div className="sidebar-sections">
        {projects.length > 0 && (
          <section className="sidebar-section">
            <button
              className="sidebar-section-trigger"
              type="button"
              aria-expanded={projectsExpanded}
              onClick={() => setProjectsExpanded((expanded) => !expanded)}
            >
              <ChevronRight
                className={projectsExpanded ? "is-expanded" : ""}
                size={15}
                aria-hidden="true"
              />
              <span>{t("sidebar.projects")}</span>
            </button>
            {projectsExpanded && (
              <div className="sidebar-section-items">
                {projects.map((project) => (
                  <div
                    className="sidebar-project"
                    key={project.id}
                    title={project.name}
                  >
                    <ProjectIcon
                      className="sidebar-project-icon"
                      icon={project.icon}
                      color={project.color}
                      size={15}
                    />
                    <span>{project.name}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {pinnedConversations.length > 0 && (
          <section className="sidebar-section">
            <button
              className="sidebar-section-trigger"
              type="button"
              aria-expanded={pinsExpanded}
              onClick={() => setPinsExpanded((expanded) => !expanded)}
            >
              <ChevronRight
                className={pinsExpanded ? "is-expanded" : ""}
                size={15}
                aria-hidden="true"
              />
              <span>{t("sidebar.pins")}</span>
            </button>
            {pinsExpanded && renderConversationItems(pinnedConversations)}
          </section>
        )}

        {unpinnedConversations.length > 0 && (
          <section className="sidebar-section">
            <button
              className="sidebar-section-trigger"
              type="button"
              aria-expanded={conversationsExpanded}
              onClick={() => setConversationsExpanded((expanded) => !expanded)}
            >
              <ChevronRight
                className={conversationsExpanded ? "is-expanded" : ""}
                size={15}
                aria-hidden="true"
              />
              <span>{t("sidebar.conversations")}</span>
            </button>
            {conversationsExpanded && renderConversationItems(unpinnedConversations)}
          </section>
        )}
      </div>

      <Menu
        className="sidebar-account-menu-root"
        open={accountMenuOpen}
        onOpenChange={handleMenuOpenChange}
      >
        <MenuContent
          open={accountMenuOpen}
          className="sidebar-account-menu"
          ariaLabel={t("sidebar.accountMenu")}
        >
          <MenuItem
            icon={<Settings2 aria-hidden="true" />}
            label={t("sidebar.settings")}
            onClick={() => {
              closeAccountMenu();
              onSettingsOpen();
            }}
          />
          <div className="menu-submenu">
            <button
              className="menu-item menu-submenu-trigger"
              type="button"
              role="menuitem"
              aria-haspopup="menu"
              aria-expanded={languageMenuOpen}
              onClick={() => setLanguageMenuOpen((open) => !open)}
            >
              <Languages size={16} aria-hidden="true" />
              <span>{t("sidebar.language")}</span>
              <ChevronRight className="menu-submenu-chevron" size={15} aria-hidden="true" />
            </button>
            <MenuContent
              open={languageMenuOpen}
              className="menu-submenu-content"
              ariaLabel={t("sidebar.language")}
            >
              <MenuRadioItem
                checked={language === "en"}
                label={t("settings.english")}
                onClick={() => selectLanguage("en")}
              />
              <MenuRadioItem
                checked={language === "pt-BR"}
                label={t("settings.portugueseBrazil")}
                onClick={() => selectLanguage("pt-BR")}
              />
            </MenuContent>
          </div>
          <MenuItem
            className="menu-item-disabled"
            icon={<LogOut aria-hidden="true" />}
            label={t("sidebar.logout")}
            title={t("sidebar.logoutUnavailable")}
            disabled
          />
        </MenuContent>
        <button
          ref={accountTriggerRef}
          className="sidebar-profile"
          aria-expanded={accountMenuOpen}
          aria-haspopup="menu"
          aria-label={t("sidebar.accountMenu")}
          onClick={() => handleMenuOpenChange(!accountMenuOpen)}
          type="button"
        >
          <span className="sidebar-profile-text">ArchHypo Flow</span>
          <ChevronDown
            className={`sidebar-chevron${accountMenuOpen ? " is-open" : ""}`}
            aria-hidden="true"
          />
        </button>
      </Menu>
    </aside>
  );
}
