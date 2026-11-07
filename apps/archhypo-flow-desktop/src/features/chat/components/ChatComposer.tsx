import {
  AuiIf,
  AttachmentPrimitive,
  ComposerPrimitive,
  useAui,
  useAuiState,
} from "@assistant-ui/react";
import { ArrowUp, FilePlus, FileText, FolderOpen, Plus, Square, X } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Menu, MenuContent, MenuItem } from "../../../components/overlay/Menu";
import {
  attachmentFolder,
  invalidExtensions,
  markFolderAttachments,
  partitionDocuments,
} from "../adapters/documentAttachmentAdapter";
import { AttachmentToast } from "./AttachmentToast";

type ChatComposerProps = {
  placeholder?: string;
  inputLabel?: string;
};

export function ChatComposer({ placeholder, inputLabel }: ChatComposerProps) {
  const { t } = useTranslation();
  const aui = useAui();
  const folderRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [notification, setNotification] = useState<{ id: number; message: string } | null>(null);
  const dismissNotification = useCallback(() => setNotification(null), []);

  const selectFiles = async (files: File[], folder: boolean) => {
    if (!files.length) return;
    const { valid, invalid, oversized } = partitionDocuments(files);
    const messages: string[] = [];
    if (invalid.length) {
      const extensions = invalidExtensions(invalid).map((extension) =>
        extension || t("chat.noExtension"),
      );
      const summary = extensions.slice(0, 8).join(", ");
      const more = extensions.length > 8 ? ` (+${extensions.length - 8})` : "";
      messages.push(t("chat.invalidExtensions", { extensions: summary + more }));
    }
    if (oversized.length) messages.push(t("chat.oversizedDocuments", { count: oversized.length }));
    const capacity = Math.max(0, 20 - aui.composer().getState().attachments.length);
    const accepted = valid.slice(0, capacity);
    if (accepted.length < valid.length) messages.push(t("chat.attachmentLimit"));
    if (messages.length) setNotification({ id: Date.now(), message: messages.join(" ") });
    if (!accepted.length) return;
    if (folder) markFolderAttachments(accepted);
    for (const file of accepted) {
      try {
        await aui.composer().addAttachment(file);
      } catch {
        setNotification({ id: Date.now(), message: t("chat.attachmentAddError") });
      }
    }
  };

  return (
    <ComposerPrimitive.Root className="chat-composer">
      <div className="chat-composer-content">
        <ComposerDocuments />
        <ComposerPrimitive.Input
          className="chat-composer-input"
          aria-label={inputLabel ?? t("chat.messageLabel")}
          placeholder={placeholder ?? t("chat.messagePlaceholder")}
          minRows={1}
          maxRows={7}
        />
        <div className="chat-composer-footer">
          <Menu open={menuOpen} onOpenChange={setMenuOpen} className="chat-attachment-menu">
            <button
              ref={menuButtonRef}
              className="chat-attachment-menu-trigger"
              type="button"
              aria-label={t("chat.addAttachments")}
              aria-expanded={menuOpen}
              aria-haspopup="menu"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <Plus size={18} aria-hidden="true" />
            </button>
            <MenuContent open={menuOpen} className="chat-attachment-menu-options" ariaLabel={t("chat.addAttachments")}>
              <div>
                <MenuItem
                  icon={<FilePlus size={16} aria-hidden="true" />}
                  label={t("chat.addFiles")}
                  onClick={() => {
                    setMenuOpen(false);
                    fileRef.current?.click();
                  }}
                />
                <MenuItem
                  icon={<FolderOpen size={16} aria-hidden="true" />}
                  label={t("chat.addFolder")}
                  onClick={() => {
                    setMenuOpen(false);
                    folderRef.current?.click();
                  }}
                />
              </div>
            </MenuContent>
          </Menu>
          <input
            ref={fileRef}
            type="file"
            multiple
            hidden
            onChange={(event) => {
              const files = Array.from(event.currentTarget.files ?? []);
              event.currentTarget.value = "";
              void selectFiles(files, false);
            }}
          />
          <input
            ref={folderRef}
            type="file"
            multiple
            hidden
            {...({ webkitdirectory: "" } as Record<string, string>)}
            onChange={(event) => {
              const files = Array.from(event.currentTarget.files ?? []);
              event.currentTarget.value = "";
              void selectFiles(files, true);
            }}
          />
          <AuiIf condition={(state) => state.thread.isRunning}>
            <ComposerPrimitive.Cancel asChild>
              <button className="chat-send-button is-cancel" type="button" aria-label={t("chat.stopResponse")} title={t("chat.stopResponse")}>
                <Square size={16} aria-hidden="true" />
              </button>
            </ComposerPrimitive.Cancel>
          </AuiIf>
          <AuiIf condition={(state) => !state.thread.isRunning}>
            <ComposerPrimitive.Send asChild>
              <button className="chat-send-button" type="button" aria-label={t("chat.sendMessage")} title={t("chat.sendMessage")}>
                <ArrowUp size={18} aria-hidden="true" />
              </button>
            </ComposerPrimitive.Send>
          </AuiIf>
        </div>
      </div>
      <AttachmentToast notification={notification} onClose={dismissNotification} />
    </ComposerPrimitive.Root>
  );
}

function ComposerDocument() {
  const { t } = useTranslation();
  return (
    <AttachmentPrimitive.Root className="chat-attachment-tile">
      <span className="chat-attachment-icon"><FileText size={18} aria-hidden="true" /></span>
      <span className="chat-attachment-name"><AttachmentPrimitive.Name /></span>
      <AttachmentPrimitive.Remove asChild>
        <button className="chat-attachment-remove" type="button" aria-label={t("chat.removeAttachment")} title={t("chat.removeAttachment")}>
          <X size={14} aria-hidden="true" />
        </button>
      </AttachmentPrimitive.Remove>
    </AttachmentPrimitive.Root>
  );
}

function ComposerDocuments() {
  const { t } = useTranslation();
  const aui = useAui();
  const attachments = useAuiState((state) => state.composer.attachments);
  const groups = new Map<string, { name: string; ids: string[] }>();
  const standalone: number[] = [];

  attachments.forEach((attachment, index) => {
    const folder = attachmentFolder(attachment.file);
    if (!folder) {
      standalone.push(index);
      return;
    }
    const group = groups.get(folder.id) ?? { name: folder.name, ids: [] };
    group.ids.push(attachment.id);
    groups.set(folder.id, group);
  });

  if (attachments.length === 0) return null;
  return (
    <div className="chat-composer-attachments">
      {standalone.map((index) => (
        <ComposerPrimitive.AttachmentByIndex key={attachments[index]?.id} index={index} components={{ Attachment: ComposerDocument }} />
      ))}
      {[...groups.entries()].map(([id, group]) => (
        <div className="chat-attachment-tile" key={id}>
            <span className="chat-attachment-icon"><FolderOpen size={18} aria-hidden="true" /></span>
            <span className="chat-attachment-name" title={group.name}>{group.name}</span>
            <button
              className="chat-attachment-remove"
              type="button"
              aria-label={t("chat.removeFolder", { name: group.name })}
              title={t("chat.removeFolder", { name: group.name })}
              onClick={() => void Promise.all(group.ids.map((attachmentId) => aui.composer().attachment({ id: attachmentId }).remove()))}
            >
              <X size={14} aria-hidden="true" />
            </button>
        </div>
      ))}
    </div>
  );
}
