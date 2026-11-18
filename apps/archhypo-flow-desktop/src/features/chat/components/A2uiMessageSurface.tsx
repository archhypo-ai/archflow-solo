import { a2uiDefaultTheme, createA2UIMessageRenderer } from "@copilotkit/react-core/v2";
import { useMemo } from "react";

const renderer = createA2UIMessageRenderer({
  theme: a2uiDefaultTheme,
  // Local interactions (such as switching tabs) work without sending a turn.
  onAction: () => null,
});
const Surface = renderer.render;

export function A2uiMessageSurface({ id, messages }: { id: string; messages: unknown }) {
  const content = useMemo(() => ({
    a2ui_operations: Array.isArray(messages) ? messages.map((operation) => {
      const create = operation?.createSurface;
      // Old checkpoints used the official schema URL instead of the CopilotKit alias.
      return operation?.version === "v0.9" &&
        create?.catalogId === "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
        ? { ...operation, createSurface: {
            ...create, catalogId: "https://a2ui.org/specification/v0_9/basic_catalog.json",
          } }
        : operation;
    }) : [],
  }), [messages]);
  if (!Array.isArray(messages) || messages.length === 0) return null;
  return (
    <div className="chat-a2ui-surface">
      <Surface
        activityType={renderer.activityType}
        content={content}
        message={{ id, role: "activity", activityType: renderer.activityType, content }}
        agent={undefined}
      />
    </div>
  );
}
