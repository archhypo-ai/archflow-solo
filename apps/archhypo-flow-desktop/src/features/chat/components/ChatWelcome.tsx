import { MessageCircle } from "lucide-react";

type ChatWelcomeProps = {
  eyebrow?: string;
  title?: string;
  description?: string;
};

export function ChatWelcome({
  eyebrow = "ARCHHYPO FLOW",
  title = "Qual incerteza arquitetural você quer explorar?",
  description = "Compartilhe o contexto da decisão e explore alternativas para sua arquitetura.",
}: ChatWelcomeProps) {
  return (
    <section className="chat-welcome" aria-labelledby="welcome-title">
      <span className="chat-welcome-icon" aria-hidden="true">
        <MessageCircle size={21} />
      </span>
      <span className="chat-eyebrow">{eyebrow}</span>
      <h2 id="welcome-title">{title}</h2>
      <p>{description}</p>
    </section>
  );
}
