import { AuiIf, ThreadPrimitive } from "@assistant-ui/react";
import "../Chat.css";
import { ChatComposer } from "./ChatComposer";
import { ChatMessageList } from "./ChatMessageList";
import { ChatWelcome } from "./ChatWelcome";

export function ChatThread() {
  return (
    <ThreadPrimitive.Root className="chat-thread-root">
      <ThreadPrimitive.Viewport className="chat-thread-viewport">
        <AuiIf condition={(state) => state.thread.isEmpty}>
          <div className="chat-empty-state">
            <ChatWelcome />
            <div className="chat-empty-composer">
              <ChatComposer />
            </div>
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
