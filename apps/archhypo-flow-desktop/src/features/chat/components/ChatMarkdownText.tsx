import { isTauri } from "@tauri-apps/api/core";
import { openUrl } from "@tauri-apps/plugin-opener";
import type { TextMessagePartComponent } from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import type { ComponentProps, MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import remarkGfm from "remark-gfm";

type MarkdownLinkProps = ComponentProps<"a">;

function MarkdownLink({ href, ...props }: MarkdownLinkProps) {
  const openExternal = (event: MouseEvent<HTMLAnchorElement>) => {
    if (!isTauri()) return;

    event.preventDefault();
    if (!href) return;

    let url: URL;
    try {
      url = new URL(href);
    } catch {
      return;
    }

    if (!["http:", "https:", "mailto:"].includes(url.protocol)) return;
    void openUrl(url.href).catch((error: unknown) => {
      console.error("Could not open external link", error);
    });
  };

  return (
    <a
      {...props}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={openExternal}
    />
  );
}

type MarkdownTableProps = ComponentProps<"table"> & { node?: unknown };

function MarkdownTable({
  children,
  className,
  node: _node,
  ...props
}: MarkdownTableProps) {
  const { t } = useTranslation();

  return (
    <div
      className="chat-markdown-table-scroll"
      role="region"
      aria-label={t("chat.tableScrollRegion")}
      tabIndex={0}
    >
      <table
        {...props}
        className={className ? `chat-markdown-table ${className}` : "chat-markdown-table"}
      >
        {children}
      </table>
    </div>
  );
}

export const ChatMarkdownText: TextMessagePartComponent = () => (
  <MarkdownTextPrimitive
    className="chat-markdown"
    remarkPlugins={[remarkGfm]}
    components={{ a: MarkdownLink, table: MarkdownTable }}
  />
);
