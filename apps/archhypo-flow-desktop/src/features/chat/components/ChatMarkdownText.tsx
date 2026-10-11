import type { TextMessagePartComponent } from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import remarkGfm from "remark-gfm";

export const ChatMarkdownText: TextMessagePartComponent = () => (
  <MarkdownTextPrimitive remarkPlugins={[remarkGfm]} />
);
