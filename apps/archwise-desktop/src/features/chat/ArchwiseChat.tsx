import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { ArchwiseThread } from "./components/ArchwiseThread";
import { useAgentChatRuntime } from "./hooks/useAgentChatRuntime";

type ArchwiseChatProps = {
  threadId: string;
  persisted: boolean;
  onConversationStarted?: (threadId: string, message: string) => void;
  onRegisterCancellation?: (
    threadId: string,
    cancel: () => Promise<void>,
  ) => () => void;
  onThreadUpdated?: () => void;
};

export function ArchwiseChat({
  threadId,
  persisted,
  onConversationStarted,
  onRegisterCancellation,
  onThreadUpdated,
}: ArchwiseChatProps) {
  const runtime = useAgentChatRuntime(threadId, {
    persisted,
    onConversationStarted,
    onRegisterCancellation,
    onThreadUpdated,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ArchwiseThread />
    </AssistantRuntimeProvider>
  );
}
