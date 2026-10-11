import { X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Menu, MenuContent } from "../../components/overlay";
import { PROJECT_ICONS, type ProjectIconId } from "./projectIcons";
import { ProjectIcon } from "./ProjectIcon";
import { PROJECT_COLORS, type Project, type ProjectColor } from "./types";
import "./CreateProjectDialog.css";

type CreateProjectDialogProps = {
  open: boolean;
  onClose: () => void;
  onCreate: (project: Project) => void;
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
}: CreateProjectDialogProps) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [icon, setIcon] = useState<ProjectIconId>(PROJECT_ICONS[0].id);
  const [color, setColor] = useState<ProjectColor>("neutral");
  const [instructions, setInstructions] = useState("");
  const [iconPickerOpen, setIconPickerOpen] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;

    setName("");
    setIcon(PROJECT_ICONS[0].id);
    setColor("neutral");
    setInstructions("");
    setIconPickerOpen(false);
    requestAnimationFrame(() => nameInputRef.current?.focus());
  }, [open]);

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
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
  }, [iconPickerOpen, onClose, open]);

  if (!open) return null;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const projectName = name.trim();
    if (!projectName) return;

    onCreate({
      id: crypto.randomUUID(),
      name: projectName,
      icon,
      color,
      instructions: instructions.trim(),
    });
    onClose();
  };

  return (
    <div
      className="project-dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      role="presentation"
    >
      <section
        className="project-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-project-title"
      >
        <header className="project-dialog-header">
          <h2 id="create-project-title">{t("projects.createTitle")}</h2>
          <button
            className="project-dialog-close"
            type="button"
            aria-label={t("projects.close")}
            title={t("projects.close")}
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <form className="project-form" onSubmit={handleSubmit}>
          <div className="project-field">
            <label htmlFor="project-name">{t("projects.nameLabel")}</label>
            <div className="project-name-row">
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

          <footer className="project-dialog-actions">
            <button
              className="project-cancel-button"
              type="button"
              onClick={onClose}
            >
              {t("projects.cancel")}
            </button>
            <button
              className="project-create-button"
              type="submit"
              disabled={!name.trim()}
            >
              {t("projects.create")}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}
