import { useCallback, useEffect, useState } from "react";
import { Sidebar } from "./components";
import { Chat } from "./features/chat";
import "./App.css";

type Theme = "day" | "night";

function initialTheme(): Theme {
  return localStorage.getItem("archhypo-flow-theme") === "day" ? "day" : "night";
}

function App() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [chatKey, setChatKey] = useState(0);
  const [activeConversationTitle, setActiveConversationTitle] = useState("");

  const handleNewChat = useCallback(() => {
    setActiveConversationTitle("");
    setChatKey((current) => current + 1);
  }, []);
  const handleConversationStarted = useCallback((title: string) => {
    setActiveConversationTitle((current) => current || title);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("archhypo-flow-theme", theme);
  }, [theme]);

  return (
    <div className="app-shell">
      <Sidebar
        theme={theme}
        activeConversationTitle={activeConversationTitle}
        onNewChat={handleNewChat}
        onToggleTheme={() =>
          setTheme((current) => (current === "night" ? "day" : "night"))
        }
      />
      <main className="main-panel">
        <header className="main-header">
          <div>
            <span className="main-header-eyebrow">ESPAÇO DE TRABALHO</span>
            <h1>Chat</h1>
          </div>
        </header>
        <Chat
          key={chatKey}
          onConversationStarted={handleConversationStarted}
        />
      </main>
    </div>
  );
}

export default App;
