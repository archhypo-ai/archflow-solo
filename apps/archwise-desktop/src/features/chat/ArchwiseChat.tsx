import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { ArchwiseThread } from "./components/ArchwiseThread";
import { useAgentChatRuntime } from "./hooks/useAgentChatRuntime";

type ArchwiseChatProps = {
  threadId: string;
  onThreadUpdated?: () => void;
};

export function ArchwiseChat({
  threadId,
  onThreadUpdated,
}: ArchwiseChatProps) {
  const runtime = useAgentChatRuntime(threadId, { onThreadUpdated });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ArchwiseThread />
    </AssistantRuntimeProvider>
  );
}
