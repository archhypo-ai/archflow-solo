import { IconArrowUp as ArrowUp, IconFilePlus as FilePlus, IconFolderOpen as FolderOpen, IconSquare as Square, IconX as X } from "@tabler/icons-react";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { markFolderAttachments, partitionDocuments } from "../adapters/documentAttachmentAdapter";

type Props = {
  running: boolean;
  disabled?: boolean;
  onSend: (text: string, files: File[]) => Promise<boolean>;
  onStop: () => void;
};

export function ChatComposer({ running, disabled, onSend, onStop }: Props) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [notice, setNotice] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const folderInput = useRef<HTMLInputElement>(null);
  const blocked = running || disabled;
  const submit = () => {
    if (blocked || (!text.trim() && !files.length)) return;
    void onSend(text.trim(), files).then((sent) => {
      if (sent) { setText(""); setFiles([]); }
    });
  };
  const add = (incoming: File[], folder: boolean) => {
    const { valid, invalid, oversized } = partitionDocuments(incoming);
    const accepted = valid.slice(0, Math.max(0, 20 - files.length));
    if (folder) markFolderAttachments(accepted);
    setFiles([...files, ...accepted]);
    setNotice([
      invalid.length ? t("chat.invalidExtensions", { extensions: invalid.map(({ name }) => name).join(", ") }) : "",
      oversized.length ? t("chat.oversizedDocuments", { count: oversized.length }) : "",
      accepted.length < valid.length ? t("chat.attachmentLimit") : "",
    ].filter(Boolean).join(" "));
  };
  return (
    <form className="chat-composer" onSubmit={(event) => { event.preventDefault(); submit(); }}>
      <div className="chat-composer-content">
        {files.map((file, index) => (
          <button type="button" key={`${file.name}-${index}`} disabled={blocked}
            onClick={() => setFiles(files.filter((_, fileIndex) => fileIndex !== index))}>
            {file.name} <X size={12} aria-hidden="true" />
          </button>
        ))}
        <textarea className="chat-composer-input" rows={2} value={text} disabled={blocked}
          aria-label={t("chat.messageLabel")} placeholder={t("chat.messagePlaceholder")}
          onChange={(event) => setText(event.target.value)} onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault(); submit();
            }
          }} />
        <div className="chat-composer-footer">
          <button type="button" className="chat-attachment-menu-trigger" disabled={blocked}
            aria-label={t("chat.addFiles")} onClick={() => fileInput.current?.click()}><FilePlus size={17} /></button>
          <button type="button" className="chat-attachment-menu-trigger" disabled={blocked}
            aria-label={t("chat.addFolder")} onClick={() => folderInput.current?.click()}><FolderOpen size={17} /></button>
          <input hidden type="file" multiple accept=".md,.txt,.docx" ref={fileInput} onChange={(event) => {
            add(Array.from(event.currentTarget.files ?? []), false); event.currentTarget.value = "";
          }} />
          <input hidden type="file" multiple {...({ webkitdirectory: "" } as Record<string, string>)} ref={folderInput} onChange={(event) => {
            add(Array.from(event.currentTarget.files ?? []), true); event.currentTarget.value = "";
          }} />
          {running ? <button type="button" className="chat-send-button is-cancel" onClick={onStop}
            aria-label={t("chat.stopResponse")}><Square size={16} /></button>
            : <button type="submit" className="chat-send-button" disabled={blocked || (!text.trim() && !files.length)}
              aria-label={t("chat.sendMessage")}><ArrowUp size={18} /></button>}
        </div>
        {notice && <p role="status">{notice}</p>}
      </div>
    </form>
  );
}
