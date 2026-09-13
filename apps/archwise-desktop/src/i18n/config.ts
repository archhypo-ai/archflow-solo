import i18n from "i18next";
import { initReactI18next } from "react-i18next";

void i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: {
        app: {
          newConversation: "New conversation",
          newConversationTitle: "New conversation",
          mainNavigation: "Main navigation",
          sections: "Sections",
          showSidebar: "Show sidebar",
          hideSidebar: "Hide sidebar",
          chat: "Chat",
          recent: "Recent",
          pinned: "Pinned",
          settings: "Settings",
          logout: "Log out",
          account: "Account",
          anonymous: "Anonymous",
          noConversations: "No conversations",
        },
        chat: {
          inputPlaceholder: "Ask ArchWISE anything...",
          message: "Message",
          addAttachment: "Add attachment",
          send: "Send message",
          validationDisclaimer:
            "ArchWISE is a research prototype. Validate generated decisions.",
        },
        settings: {
          sections: "Settings sections",
          title: "Settings",
          close: "Close settings",
          general: "General",
          generalDescription:
            "Manage the appearance and behavior of the desktop application.",
          appearance: "Appearance",
          appearanceDescription: "Choose how ArchWISE should look.",
          system: "System",
          light: "Light",
          dark: "Dark",
          language: "Language",
          languageDescription: "Choose the language used by ArchWISE.",
          english: "English",
          portuguese: "Portuguese (Brazil)",
          agent: "Agent",
          agentDescription:
            "Configure the agents used to reason about your architecture.",
          execution: "Execution",
          agentExecutionDescription:
            "Agent configuration will be available here as execution profiles are introduced.",
          rootAgent: "Root agent",
          rootAgentDescription: "The default agent for new conversations.",
          solo: "Solo",
        },
      },
    },
    "pt-BR": {
      translation: {
        app: {
          newConversation: "Nova conversa",
          newConversationTitle: "Nova conversa",
          mainNavigation: "Navegação principal",
          sections: "Seções",
          showSidebar: "Mostrar barra lateral",
          hideSidebar: "Ocultar barra lateral",
          chat: "Chat",
          recent: "Recentes",
          pinned: "Fixados",
          settings: "Configurações",
          logout: "Sair",
          account: "Conta",
          anonymous: "Anônimo",
          noConversations: "Nenhuma conversa",
        },
        chat: {
          inputPlaceholder: "Pergunte qualquer coisa ao ArchWISE...",
          message: "Mensagem",
          addAttachment: "Adicionar anexo",
          send: "Enviar mensagem",
          validationDisclaimer:
            "O ArchWISE é um protótipo de pesquisa. Valide as decisões geradas.",
        },
        settings: {
          sections: "Seções de configurações",
          title: "Configurações",
          close: "Fechar configurações",
          general: "Geral",
          generalDescription:
            "Gerencie a aparência e o comportamento do aplicativo desktop.",
          appearance: "Aparência",
          appearanceDescription: "Escolha a aparência do ArchWISE.",
          system: "Sistema",
          light: "Claro",
          dark: "Escuro",
          language: "Idioma",
          languageDescription: "Escolha o idioma usado pelo ArchWISE.",
          english: "Inglês",
          portuguese: "Português (Brasil)",
          agent: "Agente",
          agentDescription:
            "Configure os agentes usados para raciocinar sobre sua arquitetura.",
          execution: "Execução",
          agentExecutionDescription:
            "A configuração estará disponível quando os perfis de execução forem introduzidos.",
          rootAgent: "Agente raiz",
          rootAgentDescription: "O agente padrão para novas conversas.",
          solo: "Solo",
        },
      },
    },
  },
  lng: "en",
  fallbackLng: "en",
  supportedLngs: ["en", "pt-BR"],
  interpolation: { escapeValue: false },
  react: { useSuspense: false },
});

export default i18n;
