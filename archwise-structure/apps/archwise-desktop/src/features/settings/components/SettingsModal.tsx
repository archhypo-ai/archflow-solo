import { Bot, Settings2, X } from "lucide-react";
import { useI18n } from "../../../i18n";
import { IconButton } from "../../../components/ui/IconButton";
import { SidebarNavItem } from "../../../components/navigation/SidebarNavItem";
import { useSettingsDialog } from "../hooks/useSettingsDialog";
import { useSettingsNavigation } from "../hooks/useSettingsNavigation";
import { AgentSettings } from "./AgentSettings";
import { GeneralSettings } from "./GeneralSettings";
import "./SettingsModal.css";

type SettingsModalProps = {
  open: boolean;
  onClose: () => void;
};

export function SettingsModal({ open, onClose }: SettingsModalProps) {
  const { t } = useI18n();
  const { activeSection, setActiveSection } = useSettingsNavigation();
  useSettingsDialog(open, onClose);

  if (!open) return null;

  return (
    <div
      className="settings-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      role="presentation"
    >
      <section
        className="settings-dialog"
        aria-labelledby="settings-dialog-title"
        aria-modal="true"
        role="dialog"
      >
        <aside className="settings-sidebar" aria-label={t("settings.sections")}>
          <div className="settings-sidebar-heading">
            <Settings2 aria-hidden="true" />
            <strong>{t("settings.title")}</strong>
          </div>
          <nav className="settings-nav" aria-label={t("settings.title")}>
            <SidebarNavItem
              active={activeSection === "general"}
              className="settings-nav-item"
              icon={<Settings2 aria-hidden="true" />}
              label={t("settings.general")}
              onClick={() => setActiveSection("general")}
            />
            <SidebarNavItem
              active={activeSection === "agent"}
              className="settings-nav-item"
              icon={<Bot aria-hidden="true" />}
              label={t("settings.agent")}
              onClick={() => setActiveSection("agent")}
            />
          </nav>
        </aside>

        <div className="settings-main">
          <header className="settings-main-header">
            <h1 id="settings-dialog-title">{t("settings.title")}</h1>
            <IconButton label={t("settings.close")} onClick={onClose}>
              <X aria-hidden="true" />
            </IconButton>
          </header>
          <div className="settings-content">
            {activeSection === "general" ? <GeneralSettings /> : <AgentSettings />}
          </div>
        </div>
      </section>
    </div>
  );
}
