import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useLocalChatRuntime } from "./hooks/useLocalChatRuntime";
import { ArchwiseThread } from "./components/ArchwiseThread";

/** Desktop chat surface. Agent communication will be injected later. */
export function ArchwiseChat() {
  const runtime = useLocalChatRuntime();

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ArchwiseThread />
    </AssistantRuntimeProvider>
  );
}
