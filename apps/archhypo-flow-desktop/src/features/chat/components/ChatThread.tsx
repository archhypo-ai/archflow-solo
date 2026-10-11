import { AuiIf, ThreadPrimitive } from "@assistant-ui/react";
import type { ReactNode } from "react";
import "../Chat.css";
import { ChatComposer } from "./ChatComposer";
import { ChatMessageList } from "./ChatMessageList";
import type { Project } from "../../projects/types";
import { ChatWelcome } from "./ChatWelcome";

type ChatThreadProps = {
  project?: Project | null;
  projectLanding?: boolean;
  projectLandingContent?: ReactNode;
};

export function ChatThread({
  project,
  projectLanding = false,
  projectLandingContent,
}: ChatThreadProps) {
  return (
    <ThreadPrimitive.Root className="chat-thread-root">
      <ThreadPrimitive.Viewport className="chat-thread-viewport">
        <AuiIf condition={(state) => state.thread.isEmpty}>
          <div className={`chat-empty-state${projectLanding ? " is-project-landing" : ""}`}>
            <ChatWelcome project={project} />
            <div className="chat-empty-composer">
              <ChatComposer />
            </div>
            {projectLanding && projectLandingContent}
          </div>
        </AuiIf>
        <AuiIf condition={(state) => !state.thread.isEmpty}>
          <ChatMessageList />
          <div className="chat-footer">
            <ChatComposer />
          </div>
        </AuiIf>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
}
