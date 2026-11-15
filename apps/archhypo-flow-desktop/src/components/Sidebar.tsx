import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  FolderPlus,
  Home,
  Layers,
  Languages,
  LogOut,
  MoreHorizontal,
  PanelLeft,
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
import type { ConversationSummary } from "../features/conversations/types";
import { Menu, MenuContent, MenuItem, MenuRadioItem } from "./overlay";
import "./Sidebar.css";

type SidebarProps = {
  accountTriggerRef: RefObject<HTMLButtonElement | null>;
  collapsed: boolean;
  onToggle: () => void;
  activeConversationId: string | null;
  activeProjectId: string | null;
  isNewConversationActive: boolean;
  isArtifactsActive: boolean;
  conversations: ConversationSummary[];
  language: AppLanguage;
  projects: Project[];
  onConversationSelect: (threadId: string) => void;
  onProjectSelect: (projectId: string) => void;
  onEditProjectSettings: (project: Project) => void;
  onDeleteProject: (project: Project) => void;
  onRenameConversation: (conversation: ConversationSummary) => void;
  onToggleConversationPin: (conversation: ConversationSummary) => void;
  onDeleteConversation: (conversation: ConversationSummary) => void;
  onNewChat: () => void;
  onArtifactsSelect: () => void;
  onNewProject: () => void;
  onLanguageChange: (language: AppLanguage) => void;
  onSettingsOpen: () => void;
  onSkillsOpen: () => void;
  onLogoutClick: () => void;
};

export function Sidebar({
  accountTriggerRef,
  collapsed,
  onToggle,
  activeConversationId,
  activeProjectId,
  isNewConversationActive,
  isArtifactsActive,
  conversations,
  language,
  projects,
  onConversationSelect,
  onProjectSelect,
  onEditProjectSettings,
  onDeleteProject,
  onRenameConversation,
  onToggleConversationPin,
  onDeleteConversation,
  onNewChat,
  onArtifactsSelect,
  onNewProject,
  onLanguageChange,
  onSettingsOpen,
  onSkillsOpen,
  onLogoutClick,
}: SidebarProps) {
  const { t } = useTranslation();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [languageMenuOpen, setLanguageMenuOpen] = useState(false);
  const [projectsExpanded, setProjectsExpanded] = useState(false);
  const [expandedProjectIds, setExpandedProjectIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [pinsExpanded, setPinsExpanded] = useState(false);
  const [conversationsExpanded, setConversationsExpanded] = useState(false);
  const [openConversationMenuId, setOpenConversationMenuId] = useState<string | null>(null);
  const [openProjectMenuId, setOpenProjectMenuId] = useState<string | null>(null);
  const pinnedConversations = conversations.filter((conversation) => conversation.pinned);
  const unpinnedConversations = conversations.filter(
    (conversation) => !conversation.pinned && conversation.projectId === null,
  );

  useEffect(() => {
    if (unpinnedConversations.length > 0) setConversationsExpanded(true);
  }, [unpinnedConversations.length]);
  useEffect(() => {
    if (pinnedConversations.length > 0) setPinsExpanded(true);
  }, [pinnedConversations.length]);
  useEffect(() => {
    if (projects.length > 0) setProjectsExpanded(true);
  }, [projects.length]);
  useEffect(() => {
    const activeConversation = conversations.find(
      (conversation) => conversation.threadId === activeConversationId,
    );
    const projectId = activeConversation?.projectId;
    if (!projectId) return;
    setExpandedProjectIds((current) => {
      if (current.has(projectId)) return current;
      return new Set(current).add(projectId);
    });
  }, [activeConversationId, conversations]);

  const renderConversationItems = (
    items: ConversationSummary[],
    projectNested = false,
  ) => (
    <div
      className={`sidebar-section-items sidebar-conversation-items${projectNested ? " sidebar-project-conversations" : ""}`}
    >
      {items.map((conversation) => {
        const isActive = conversation.threadId === activeConversationId;
        const menuOpen = openConversationMenuId === conversation.threadId;
        return (
          <div
            className={`sidebar-conversation-row${isActive ? " is-active" : ""}`}
            key={conversation.threadId}
          >
            <button
              className={`sidebar-conversation${projectNested ? " sidebar-project-conversation" : ""}`}
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
                {(!conversation.projectId || conversation.pinned) && (
                  <MenuItem
                    icon={conversation.pinned ? <PinOff aria-hidden="true" /> : <Pin aria-hidden="true" />}
                    label={t(conversation.pinned ? "conversations.unpin" : "conversations.pin")}
                    onClick={() => {
                      setOpenConversationMenuId(null);
                      onToggleConversationPin(conversation);
                    }}
                  />
                )}
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
    <aside
      className={`sidebar${collapsed ? " is-collapsed" : ""}`}
      aria-label={t("sidebar.navigationLabel")}
    >
      <div className="sidebar-header">
        <button
          className="sidebar-toggle"
          type="button"
          aria-label={t(collapsed ? "sidebar.expandSidebar" : "sidebar.collapseSidebar")}
          title={t(collapsed ? "sidebar.expandSidebar" : "sidebar.collapseSidebar")}
          onClick={onToggle}
        >
          <PanelLeft size={17} aria-hidden="true" />
        </button>
        <strong className="sidebar-brand">ArchHypo Flow</strong>
      </div>
      <div className="sidebar-primary-actions">
        <button
          className={`sidebar-action-button${isNewConversationActive ? " is-active" : ""}`}
          onClick={onNewChat}
          type="button"
          aria-pressed={isNewConversationActive}
          aria-label={t("sidebar.newConversation")}
          title={t("sidebar.newConversation")}
        >
          <SquarePen size={17} aria-hidden="true" />
          <span>{t("sidebar.newConversation")}</span>
        </button>
        <button
          className="sidebar-action-button"
          onClick={onNewProject}
          type="button"
          aria-label={t("sidebar.newProject")}
          title={t("sidebar.newProject")}
        >
          <FolderPlus size={17} aria-hidden="true" />
          <span>{t("sidebar.newProject")}</span>
        </button>
        <button
          className={`sidebar-action-button${isArtifactsActive ? " is-active" : ""}`}
          onClick={onArtifactsSelect}
          type="button"
          aria-pressed={isArtifactsActive}
          aria-label={t("sidebar.artifacts")}
          title={t("sidebar.artifacts")}
        >
          <Layers size={17} aria-hidden="true" />
          <span>{t("sidebar.artifacts")}</span>
        </button>
        <button className="sidebar-action-button" onClick={onSkillsOpen} type="button" aria-label="Skills" title="Skills">
          <BookOpen size={17} aria-hidden="true" /><span>Skills</span>
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
              <div
                className="sidebar-section-items sidebar-project-items"
              >
                {projects.map((project) => {
                  const active = project.id === activeProjectId;
                  const menuOpen = openProjectMenuId === project.id;
                  const expanded = expandedProjectIds.has(project.id);
                  const conversationsId = `project-conversations-${project.id}`;
                  const projectConversations = conversations.filter(
                    (conversation) =>
                      conversation.projectId === project.id && !conversation.pinned,
                  );
                  return (
                    <div className="sidebar-project-group" key={project.id}>
                      <div
                        className={`sidebar-project-row${active ? " is-active" : ""}`}
                      >
                        <button
                          className="sidebar-project"
                          type="button"
                          title={project.name}
                          aria-current={active ? "page" : undefined}
                          aria-expanded={expanded}
                          aria-controls={conversationsId}
                          onClick={() =>
                            setExpandedProjectIds((current) => {
                              const next = new Set(current);
                              if (next.has(project.id)) next.delete(project.id);
                              else next.add(project.id);
                              return next;
                            })
                          }
                        >
                          <ChevronRight
                            className={`sidebar-project-chevron${expanded ? " is-expanded" : ""}`}
                            size={12}
                            aria-hidden="true"
                          />
                          <ProjectIcon
                            className="sidebar-project-icon"
                            icon={project.icon}
                            color={project.color}
                            size={15}
                          />
                          <span>{project.name}</span>
                        </button>
                        <div className="sidebar-project-actions">
                          <button
                            className="sidebar-project-home-trigger"
                            type="button"
                            title={t("projects.home")}
                            aria-label={t("projects.home")}
                            onClick={() => onProjectSelect(project.id)}
                          >
                            <SquarePen size={16} aria-hidden="true" />
                          </button>
                          <Menu
                            className="sidebar-project-menu-root"
                            open={menuOpen}
                            onOpenChange={(open) =>
                              setOpenProjectMenuId(open ? project.id : null)
                            }
                          >
                            <button
                              className="sidebar-project-menu-trigger"
                              type="button"
                              aria-label={t("projects.actions")}
                              aria-haspopup="menu"
                              aria-expanded={menuOpen}
                              onClick={() =>
                                setOpenProjectMenuId(menuOpen ? null : project.id)
                              }
                            >
                              <MoreHorizontal size={16} aria-hidden="true" />
                            </button>
                            <MenuContent
                              open={menuOpen}
                              className="sidebar-project-menu"
                              ariaLabel={t("projects.actions")}
                            >
                              <MenuItem
                                icon={<Home aria-hidden="true" />}
                                label={t("projects.home")}
                                onClick={() => {
                                  setOpenProjectMenuId(null);
                                  onProjectSelect(project.id);
                                }}
                              />
                              <MenuItem
                                icon={<Settings2 aria-hidden="true" />}
                                label={t("projects.settings")}
                                onClick={() => {
                                  setOpenProjectMenuId(null);
                                  onEditProjectSettings(project);
                                }}
                              />
                              <MenuItem
                                className="menu-item-danger"
                                icon={<Trash2 aria-hidden="true" />}
                                label={t("conversations.delete")}
                                onClick={() => {
                                  setOpenProjectMenuId(null);
                                  onDeleteProject(project);
                                }}
                              />
                            </MenuContent>
                          </Menu>
                        </div>
                      </div>
                      <div id={conversationsId} hidden={!expanded}>
                        {expanded &&
                          (projectConversations.length > 0 ? (
                            renderConversationItems(projectConversations, true)
                          ) : (
                            <span className="sidebar-empty-state">
                              {t("projects.noChats")}
                            </span>
                          ))}
                      </div>
                    </div>
                  );
                })}
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
            icon={<LogOut aria-hidden="true" />}
            label={t("sidebar.logout")}
            title={t("sidebar.logoutPreview")}
            onClick={() => {
              closeAccountMenu();
              onLogoutClick();
            }}
          />
        </MenuContent>
        <button
          ref={accountTriggerRef}
          className="sidebar-profile"
          aria-expanded={accountMenuOpen}
          aria-haspopup="menu"
          aria-label={t("sidebar.accountMenu")}
          title={t("sidebar.accountMenu")}
          onClick={() => handleMenuOpenChange(!accountMenuOpen)}
          type="button"
        >
          <span className="sidebar-avatar" aria-hidden="true">A</span>
          <span className="sidebar-profile-text">{t("sidebar.anonymous")}</span>
          <ChevronDown
            className={`sidebar-chevron${accountMenuOpen ? " is-open" : ""}`}
            aria-hidden="true"
          />
        </button>
      </Menu>
    </aside>
  );
}
