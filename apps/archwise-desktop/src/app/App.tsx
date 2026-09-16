import { useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { ArchwiseChat } from "../features/chat";
import { useConversations } from "../features/conversations";
import { SettingsModal } from "../features/settings";
import { ThemeProvider } from "../features/theme";
import { I18nProvider, useI18n } from "../i18n";

function AppContent() {
  const { t } = useI18n();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const {
    conversations,
    activeConversationId,
    newConversation,
    ensureConversation,
    refreshConversations,
    selectConversation,
    togglePinned,
    deleteConversation,
  } = useConversations();
  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  return (
    <>
      <AppShell
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewConversation={newConversation}
        onSettingsOpen={() => setSettingsOpen(true)}
        onConversationSelect={selectConversation}
        onConversationPinToggle={togglePinned}
        onConversationDelete={deleteConversation}
      >
        <header className="content-header">
          <h1>{activeConversation?.label ?? t("app.newConversation")}</h1>
        </header>
        <main className="chat-area">
          <ArchwiseChat
            key={activeConversationId ?? "new-conversation"}
            threadId={activeConversationId ?? "new-conversation"}
            persisted={Boolean(activeConversation)}
            onConversationStarted={ensureConversation}
            onThreadUpdated={refreshConversations}
          />
        </main>
      </AppShell>
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </>
  );
}

export default function App() {
  return (
    <I18nProvider>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </I18nProvider>
  );
}
