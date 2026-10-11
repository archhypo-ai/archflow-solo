import { useTranslation } from "react-i18next";
import { ProjectIcon } from "../../projects/ProjectIcon";
import type { Project } from "../../projects/types";

type ChatWelcomeProps = {
  title?: string;
  description?: string;
  project?: Project | null;
};

export function ChatWelcome({
  title,
  description,
  project,
}: ChatWelcomeProps) {
  const { t } = useTranslation();

  return (
    <section className="chat-welcome" aria-labelledby="welcome-title">
      {project ? (
        <div className="chat-welcome-project-heading">
          <ProjectIcon icon={project.icon} color={project.color} size={30} />
          <h2 id="welcome-title">{project.name}</h2>
        </div>
      ) : (
        <h2 id="welcome-title">{title ?? t("chat.welcomeTitle")}</h2>
      )}
      {project ? (
        project.instructions.trim() && (
          <p className="chat-welcome-project-instructions">
            {project.instructions}
          </p>
        )
      ) : (
        <p>{description ?? t("chat.welcomeDescription")}</p>
      )}
    </section>
  );
}
