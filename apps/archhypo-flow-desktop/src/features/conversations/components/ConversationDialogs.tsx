import { IconAlertTriangle as AlertTriangle, IconPencil as Pencil, IconTrash as Trash2 } from "@tabler/icons-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import type { ConversationSummary } from "../types";
import "./ConversationDialogs.css";

type RenameConversationDialogProps = {
  conversation: ConversationSummary | null;
  onClose: () => void;
  onSave: (threadId: string, title: string) => Promise<void>;
};

export function RenameConversationDialog({
  conversation,
  onClose,
  onSave,
}: RenameConversationDialogProps) {
  const { t } = useTranslation();
  const [title, setTitle] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [hasError, setHasError] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!conversation) return;
    setTitle(conversation.title);
    setHasError(false);
    requestAnimationFrame(() => inputRef.current?.select());
  }, [conversation]);

  useDialogEscape(Boolean(conversation), onClose);
  if (!conversation) return null;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle || isSaving) return;

    setIsSaving(true);
    setHasError(false);
    try {
      await onSave(conversation.threadId, cleanTitle);
    } catch {
      setHasError(true);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="conversation-dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isSaving) onClose();
      }}
      role="presentation"
    >
      <section
        className="conversation-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="rename-conversation-title"
      >
        <header className="conversation-dialog-header">
          <Pencil size={17} aria-hidden="true" />
          <h2 id="rename-conversation-title">{t("conversations.renameTitle")}</h2>
        </header>
        <form onSubmit={submit}>
          <label className="conversation-dialog-label" htmlFor="conversation-title-input">
            {t("conversations.titleLabel")}
          </label>
          <input
            ref={inputRef}
            id="conversation-title-input"
            className="conversation-dialog-input"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={80}
            autoComplete="off"
            required
          />
          {hasError && (
            <p className="conversation-dialog-error" role="alert">
              {t("conversations.actionError")}
            </p>
          )}
          <footer className="conversation-dialog-actions">
            <button
              className="conversation-dialog-button is-secondary"
              type="button"
              onClick={onClose}
              disabled={isSaving}
            >
              {t("conversations.cancel")}
            </button>
            <button
              className="conversation-dialog-button is-primary"
              type="submit"
              disabled={!title.trim() || isSaving}
            >
              {t("conversations.save")}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

type DeleteConversationDialogProps = {
  conversation: ConversationSummary | null;
  onClose: () => void;
  onConfirm: (threadId: string) => Promise<void>;
};

export function DeleteConversationDialog({
  conversation,
  onClose,
  onConfirm,
}: DeleteConversationDialogProps) {
  const { t } = useTranslation();
  const [isDeleting, setIsDeleting] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (conversation) setHasError(false);
  }, [conversation]);
  useDialogEscape(Boolean(conversation), onClose);
  if (!conversation) return null;

  const confirm = async () => {
    if (isDeleting) return;
    setIsDeleting(true);
    setHasError(false);
    try {
      await onConfirm(conversation.threadId);
    } catch {
      setHasError(true);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div
      className="conversation-dialog-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isDeleting) onClose();
      }}
      role="presentation"
    >
      <section
        className="conversation-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-conversation-title"
        aria-describedby="delete-conversation-description"
      >
        <header className="conversation-dialog-header is-danger">
          <AlertTriangle size={18} aria-hidden="true" />
          <h2 id="delete-conversation-title">{t("conversations.deleteTitle")}</h2>
        </header>
        <p id="delete-conversation-description" className="conversation-dialog-description">
          {t("conversations.deleteDescription", { title: conversation.title })}
        </p>
        {hasError && (
          <p className="conversation-dialog-error" role="alert">
            {t("conversations.actionError")}
          </p>
        )}
        <footer className="conversation-dialog-actions">
          <button
            className="conversation-dialog-button is-secondary"
            type="button"
            onClick={onClose}
            disabled={isDeleting}
          >
            {t("conversations.cancel")}
          </button>
          <button
            className="conversation-dialog-button is-danger"
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

function useDialogEscape(open: boolean, onClose: () => void) {
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);
}
