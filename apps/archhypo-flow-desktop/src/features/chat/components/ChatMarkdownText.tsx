import { isTauri } from "@tauri-apps/api/core";
import { openUrl } from "@tauri-apps/plugin-opener";
import type { TextMessagePartComponent } from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import type { ComponentProps, MouseEvent } from "react";
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

export const ChatMarkdownText: TextMessagePartComponent = () => (
  <MarkdownTextPrimitive
    remarkPlugins={[remarkGfm]}
    components={{ a: MarkdownLink }}
  />
);
