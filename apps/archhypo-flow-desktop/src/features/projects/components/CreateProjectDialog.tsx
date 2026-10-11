import { FolderPlus, Settings2, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Menu, MenuContent } from "../../../components/overlay";
import { PROJECT_ICONS, type ProjectIconId } from "../projectIcons";
import { ProjectIcon } from "./ProjectIcon";
import { PROJECT_COLORS, type Project, type ProjectColor } from "../types";
import "./CreateProjectDialog.css";

type CreateProjectDialogProps = {
  open: boolean;
  onClose: () => void;
  project?: Project | null;
  onCreate: (project: Project) => Promise<void>;
  onUpdate?: (project: Project) => Promise<void>;
};

const colorLabelKeys: Record<ProjectColor, string> = {
  neutral: "projects.colorNeutral",
  red: "projects.colorRed",
  orange: "projects.colorOrange",
  yellow: "projects.colorYellow",
  green: "projects.colorGreen",
  blue: "projects.colorBlue",
  purple: "projects.colorPurple",
  pink: "projects.colorPink",
};

export function CreateProjectDialog({
  open,
  onClose,
  onCreate,
  onUpdate,
  project = null,
}: CreateProjectDialogProps) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [icon, setIcon] = useState<ProjectIconId>(PROJECT_ICONS[0].id);
  const [color, setColor] = useState<ProjectColor>("neutral");
  const [instructions, setInstructions] = useState("");
  const [iconPickerOpen, setIconPickerOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;

    setName(project?.name ?? "");
    setIcon(project?.icon ?? PROJECT_ICONS[0].id);
    setColor(project?.color ?? "neutral");
    setInstructions(project?.instructions ?? "");
    setIconPickerOpen(false);
    setIsCreating(false);
    setCreateError(false);
    requestAnimationFrame(() => nameInputRef.current?.focus());
  }, [open, project]);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || isCreating) return;
      if (iconPickerOpen) {
        setIconPickerOpen(false);
        event.preventDefault();
        event.stopImmediatePropagation();
        return;
      }
      onClose();
    };

    document.addEventListener("keydown", handleKeyDown, true);
    return () => document.removeEventListener("keydown", handleKeyDown, true);
  }, [iconPickerOpen, isCreating, onClose, open]);

  if (!open) return null;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const projectName = name.trim();
    if (!projectName || isCreating) return;

    setIsCreating(true);
    setCreateError(false);
    try {
      const updatedProject: Project = {
        id: project?.id ?? crypto.randomUUID(),
        name: projectName,
        icon,
        color,
        instructions: instructions.trim(),
      };
      if (project) {
        if (!onUpdate) throw new Error("Project settings update is unavailable");
        await onUpdate(updatedProject);
      } else {
        await onCreate(updatedProject);
      }
      onClose();
    } catch {
      setCreateError(true);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div
      className="project-dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isCreating) onClose();
      }}
      role="presentation"
    >
      <section
        className="project-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-form-title"
      >
        <header className="project-dialog-header">
          <div className="project-dialog-title">
            {project ? (
              <Settings2 className="project-dialog-title-icon" size={18} aria-hidden="true" />
            ) : (
              <FolderPlus className="project-dialog-title-icon" size={18} aria-hidden="true" />
            )}
            <h2 id="project-form-title">
              {t(project ? "projects.settingsTitle" : "projects.createTitle")}
            </h2>
          </div>
          <button
            className="project-dialog-close"
            type="button"
            aria-label={t("projects.close")}
            title={t("projects.close")}
            onClick={onClose}
            disabled={isCreating}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <form className="project-form" onSubmit={handleSubmit}>
          <div className="project-field">
            <label htmlFor="project-name">{t("projects.nameLabel")}</label>
            <div className="project-name-row">
              <Menu
                className="project-icon-menu"
                open={iconPickerOpen}
                onOpenChange={setIconPickerOpen}
              >
                <button
                  className="project-icon-trigger"
                  type="button"
                  aria-label={t("projects.chooseIcon")}
                  aria-expanded={iconPickerOpen}
                  aria-haspopup="menu"
                  title={t("projects.chooseIcon")}
                  onClick={() => setIconPickerOpen((current) => !current)}
                >
                  <ProjectIcon icon={icon} color={color} size={19} />
                </button>
                <MenuContent
                  open={iconPickerOpen}
                  className="project-icon-picker"
                  ariaLabel={t("projects.chooseIcon")}
                >
                  <div
                    className="project-color-options"
                    role="group"
                    aria-label={t("projects.chooseColor")}
                  >
                    {PROJECT_COLORS.map((projectColor) => (
                      <button
                        key={projectColor}
                        className="project-color-option"
                        type="button"
                        role="menuitemradio"
                        aria-checked={color === projectColor}
                        aria-label={t(colorLabelKeys[projectColor])}
                        title={t(colorLabelKeys[projectColor])}
                        data-project-color={projectColor}
                        onClick={() => setColor(projectColor)}
                      >
                        <span aria-hidden="true" />
                      </button>
                    ))}
                  </div>
                  <div
                    className="project-icon-grid"
                    role="group"
                    aria-label={t("projects.chooseIcon")}
                  >
                    {PROJECT_ICONS.map(({ id, Icon }, index) => (
                      <button
                        key={id}
                        className={`project-icon-option${icon === id ? " is-selected" : ""}`}
                        type="button"
                        role="menuitemradio"
                        aria-checked={icon === id}
                        aria-label={t("projects.iconOption", {
                          number: index + 1,
                        })}
                        title={t("projects.iconOption", {
                          number: index + 1,
                        })}
                        onClick={() => {
                          setIcon(id);
                          setIconPickerOpen(false);
                        }}
                      >
                        <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
                      </button>
                    ))}
                  </div>
                </MenuContent>
              </Menu>
              <input
                ref={nameInputRef}
                id="project-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder={t("projects.namePlaceholder")}
                maxLength={80}
                autoComplete="off"
                required
              />
            </div>
          </div>

          <div className="project-field project-instructions-field">
            <label htmlFor="project-instructions">
              {t("projects.instructionsLabel")}
            </label>
            <p>{t("projects.instructionsDescription")}</p>
            <textarea
              id="project-instructions"
              value={instructions}
              onChange={(event) => setInstructions(event.target.value)}
              placeholder={t("projects.instructionsPlaceholder")}
              rows={5}
            />
          </div>

          {createError && (
            <p className="project-create-error" role="alert">
              {t(project ? "projects.settingsError" : "projects.createError")}
            </p>
          )}
          <footer className="project-dialog-actions">
            <button
              className="project-cancel-button"
              type="button"
              onClick={onClose}
              disabled={isCreating}
            >
              {t("projects.cancel")}
            </button>
            <button
              className="project-create-button"
              type="submit"
              disabled={!name.trim() || isCreating}
            >
              {t(project ? "projects.saveSettings" : "projects.create")}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
