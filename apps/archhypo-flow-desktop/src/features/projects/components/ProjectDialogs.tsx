import { IconAlertTriangle as AlertTriangle, IconTrash as Trash2 } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Project } from "../types";
import "./ProjectDialogs.css";

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
