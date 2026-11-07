import { AlertTriangle, X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "react-i18next";

type AttachmentToastProps = {
  notification: { id: number; message: string } | null;
  onClose: () => void;
};

export function AttachmentToast({ notification, onClose }: AttachmentToastProps) {
  const { t } = useTranslation();
  useEffect(() => {
    if (!notification) return;
    const timer = window.setTimeout(onClose, 8_000);
    return () => window.clearTimeout(timer);
  }, [notification, onClose]);
  if (!notification) return null;

  return createPortal(
    <div className="attachment-toast" role="alert">
      <AlertTriangle size={18} aria-hidden="true" />
      <span>{notification.message}</span>
      <button type="button" onClick={onClose} aria-label={t("chat.dismissToast")}>
        <X size={16} aria-hidden="true" />
      </button>
    </div>,
    document.body,
  );
}
