import {
  AssistantRuntimeProvider,
  useLocalRuntime,
} from "@assistant-ui/react";
import { useMemo } from "react";
import { createDemoChatModel } from "./adapters/demoChatModel";
import { ChatThread } from "./components/ChatThread";

type ChatProps = {
  onConversationStarted: (title: string) => void;
};

export function Chat({ onConversationStarted }: ChatProps) {
  const chatModel = useMemo(
    () => createDemoChatModel({ onConversationStarted }),
    [onConversationStarted],
  );
  const runtime = useLocalRuntime(chatModel);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatThread />
    </AssistantRuntimeProvider>
  );
}
