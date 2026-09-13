import { AppShell } from "../components/layout/AppShell";
import { ArchwiseChat } from "../features/chat";
import { useConversations } from "../features/conversations";
import { I18nProvider } from "../i18n/I18nProvider";
import { ThemeProvider } from "../features/theme";

function AppContent() {
  const {
    conversations,
    activeConversationId,
    newConversation,
    selectConversation,
  } = useConversations();
  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  return (
    <AppShell
      conversations={conversations}
      activeConversationId={activeConversationId}
      onNewConversation={newConversation}
      onConversationSelect={selectConversation}
    >
      <header className="content-header">
        <h1>{activeConversation?.label ?? "New conversation"}</h1>
      </header>
      <main className="chat-area">
        <ArchwiseChat key={activeConversationId ?? "new-conversation"} />
      </main>
    </AppShell>
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
