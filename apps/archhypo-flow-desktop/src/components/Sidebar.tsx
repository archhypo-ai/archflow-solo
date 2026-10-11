import {
  ChevronDown,
  ChevronRight,
  FolderPlus,
  Languages,
  LogOut,
  MessageSquareText,
  Settings2,
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
  conversations: ConversationSummary[];
  language: AppLanguage;
  projects: Project[];
  onConversationSelect: (threadId: string) => void;
  onNewChat: () => void;
  onNewProject: () => void;
  onLanguageChange: (language: AppLanguage) => void;
  onSettingsOpen: () => void;
};

export function Sidebar({
  accountTriggerRef,
  activeConversationId,
  conversations,
  language,
  projects,
  onConversationSelect,
  onNewChat,
  onNewProject,
  onLanguageChange,
  onSettingsOpen,
}: SidebarProps) {
  const { t } = useTranslation();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);
  const [projectsExpanded, setProjectsExpanded] = useState(false);
  const [conversationsExpanded, setConversationsExpanded] = useState(false);

  useEffect(() => {
    if (conversations.length > 0) setConversationsExpanded(true);
  }, [conversations.length]);
  useEffect(() => {
    if (projects.length > 0) setProjectsExpanded(true);
  }, [projects.length]);

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
        <button className="sidebar-action-button" onClick={onNewChat} type="button">
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
          {projectsExpanded && projects.length > 0 && (
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
          {conversationsExpanded && conversations.length > 0 && (
            <div className="sidebar-section-items">
              {conversations.map((conversation) => {
                const isActive = conversation.threadId === activeConversationId;
                return (
                  <button
                    className={`sidebar-conversation${isActive ? " is-active" : ""}`}
                    key={conversation.threadId}
                    type="button"
                    title={conversation.title}
                    aria-current={isActive ? "page" : undefined}
                    onClick={() => onConversationSelect(conversation.threadId)}
                  >
                    <MessageSquareText size={14} aria-hidden="true" />
                    <span>{conversation.title}</span>
                  </button>
                );
              })}
            </div>
          )}
        </section>
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
