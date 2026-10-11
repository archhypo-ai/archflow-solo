import { useTranslation } from "react-i18next";

type ChatWelcomeProps = {
  title?: string;
  description?: string;
};

export function ChatWelcome({ title, description }: ChatWelcomeProps) {
  const { t } = useTranslation();

  return (
    <section className="chat-welcome" aria-labelledby="welcome-title">
      <h2 id="welcome-title">{title ?? t("chat.welcomeTitle")}</h2>
      <p>{description ?? t("chat.welcomeDescription")}</p>
    </section>
  );
}
