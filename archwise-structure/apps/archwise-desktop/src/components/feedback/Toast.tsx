import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";
import {
  CircleAlert,
  CircleCheck,
  Info,
  TriangleAlert,
  X,
  type LucideIcon,
} from "lucide-react";
import { useI18n } from "../../i18n";
import "./Toast.css";

export const TOAST_DURATION_MS = 3000;

export type ToastTone = "success" | "error" | "warning" | "info";

type ToastOptions = {
  message: string;
  tone?: ToastTone;
  duration?: number;
};

type ToastRecord = Required<ToastOptions> & {
  id: string;
};

type ToastApi = {
  show: (options: ToastOptions) => string;
  success: (message: string) => string;
  error: (message: string) => string;
  warning: (message: string) => string;
  info: (message: string) => string;
  dismiss: (id: string) => void;
};

const ToastContext = createContext<ToastApi | null>(null);

const toneIcons: Record<ToastTone, LucideIcon> = {
  success: CircleCheck,
  error: CircleAlert,
  warning: TriangleAlert,
  info: Info,
};

let nextToastId = 0;

function createToastId() {
  nextToastId += 1;
  return `toast-${Date.now()}-${nextToastId}`;
}

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: ToastRecord;
  onDismiss: (id: string) => void;
}) {
  const { t } = useI18n();
  const Icon = toneIcons[toast.tone];

  useEffect(() => {
    const timeout = window.setTimeout(
      () => onDismiss(toast.id),
      toast.duration,
    );
    return () => window.clearTimeout(timeout);
  }, [onDismiss, toast.duration, toast.id]);

  return (
    <article
      className="toast"
      data-tone={toast.tone}
      role={toast.tone === "error" ? "alert" : "status"}
    >
      <Icon className="toast-icon" aria-hidden="true" />
      <span className="toast-message">{toast.message}</span>
      <button
        className="toast-dismiss"
        type="button"
        aria-label={t("toast.close")}
        title={t("toast.close")}
        onClick={() => onDismiss(toast.id)}
      >
        <X aria-hidden="true" />
      </button>
    </article>
  );
}

export function ToastProvider({ children }: PropsWithChildren) {
  const { t } = useI18n();
  const [toasts, setToasts] = useState<ToastRecord[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const show = useCallback((options: ToastOptions) => {
    const toast: ToastRecord = {
      id: createToastId(),
      message: options.message,
      tone: options.tone ?? "info",
      duration: options.duration ?? TOAST_DURATION_MS,
    };
    setToasts((current) => [...current, toast]);
    return toast.id;
  }, []);

  const value = useMemo<ToastApi>(
    () => ({
      show,
      success: (message) => show({ message, tone: "success" }),
      error: (message) => show({ message, tone: "error" }),
      warning: (message) => show({ message, tone: "warning" }),
      info: (message) => show({ message, tone: "info" }),
      dismiss,
    }),
    [dismiss, show],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region" aria-label={t("toast.regionLabel")}>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside ToastProvider");
  return context;
}
