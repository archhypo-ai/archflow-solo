import { AlertTriangle, Pencil, Trash2 } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import type { Project } from "./types";
import "./ProjectDialogs.css";

type RenameProjectDialogProps = {
  project: Project | null;
  onClose: () => void;
  onSave: (projectId: string, name: string) => Promise<void>;
};

export function RenameProjectDialog({ project, onClose, onSave }: RenameProjectDialogProps) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [hasError, setHasError] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!project) return;
    setName(project.name);
    setHasError(false);
    requestAnimationFrame(() => inputRef.current?.select());
  }, [project]);
  useDialogEscape(Boolean(project), isSaving, onClose);
  if (!project) return null;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanName = name.trim();
    if (!cleanName || isSaving) return;
    setIsSaving(true);
    setHasError(false);
    try {
      await onSave(project.id, cleanName);
    } catch {
      setHasError(true);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="project-management-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isSaving) onClose();
      }}
    >
      <section
        className="project-management-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rename-project-title"
      >
        <header className="project-management-header">
          <Pencil size={17} aria-hidden="true" />
          <h2 id="rename-project-title">{t("projects.renameTitle")}</h2>
        </header>
        <form onSubmit={submit}>
          <label className="project-management-label" htmlFor="rename-project-name">
            {t("projects.nameLabel")}
          </label>
          <input
            ref={inputRef}
            id="rename-project-name"
            className="project-management-input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={80}
            autoComplete="off"
            required
          />
          {hasError && (
            <p className="project-management-error" role="alert">
              {t("projects.renameError")}
            </p>
          )}
          <footer className="project-management-actions">
            <button
              className="project-management-button is-secondary"
              type="button"
              onClick={onClose}
              disabled={isSaving}
            >
              {t("conversations.cancel")}
            </button>
            <button
              className="project-management-button is-primary"
              type="submit"
              disabled={!name.trim() || isSaving}
            >
              {t("conversations.save")}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

type DeleteProjectDialogProps = {
  project: Project | null;
  conversationCount: number;
  onClose: () => void;
  onConfirm: (projectId: string) => Promise<void>;
};

export function DeleteProjectDialog({
  project,
  conversationCount,
  onClose,
  onConfirm,
}: DeleteProjectDialogProps) {
  const { t } = useTranslation();
  const [isDeleting, setIsDeleting] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (project) setHasError(false);
  }, [project]);
  useDialogEscape(Boolean(project), isDeleting, onClose);
  if (!project) return null;

  const confirm = async () => {
    if (isDeleting) return;
    setIsDeleting(true);
    setHasError(false);
    try {
      await onConfirm(project.id);
    } catch {
      setHasError(true);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      className="project-management-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isDeleting) onClose();
      }}
    >
      <section
        className="project-management-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-project-title"
        aria-describedby="delete-project-description"
      >
        <header className="project-management-header is-danger">
          <AlertTriangle size={18} aria-hidden="true" />
          <h2 id="delete-project-title">{t("projects.deleteTitle")}</h2>
        </header>
        <p id="delete-project-description" className="project-management-description">
          {t("projects.deleteDescription", {
            title: project.name,
            count: conversationCount,
          })}
        </p>
        {hasError && (
          <p className="project-management-error" role="alert">
            {t("projects.deleteError")}
          </p>
        )}
        <footer className="project-management-actions">
          <button
            className="project-management-button is-secondary"
            type="button"
            onClick={onClose}
            disabled={isDeleting}
          >
            {t("conversations.cancel")}
          </button>
          <button
            className="project-management-button is-danger"
            type="button"
            onClick={() => void confirm()}
            disabled={isDeleting}
          >
            <Trash2 size={15} aria-hidden="true" />
            {t("conversations.delete")}
          </button>
        </footer>
      </section>
    </div>
  );
}

function useDialogEscape(open: boolean, isBusy: boolean, onClose: () => void) {
  useEffect(() => {
    if (!open || isBusy) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isBusy, onClose, open]);
}
