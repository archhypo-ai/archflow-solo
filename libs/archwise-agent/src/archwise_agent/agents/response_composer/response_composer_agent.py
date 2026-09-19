"""Human-facing response agent."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from archwise_agent.core import UserResponse

SYSTEM_PROMPT = """\
You are the ArchWise Response Composer Agent.

Produce the final human-facing answer for the current conversation.

Rules:
- Answer the latest user request directly and naturally.
- Use the conversation history to resolve references and follow-up questions.
- If an ArchWise analysis result is supplied, explain it clearly instead of
  exposing JSON, internal state, routing decisions, or agent names.
- Preserve the important content: the normalized uncertainty, hypothesis,
  classification, and technical plan when they are present.
- Use the same language as the latest user request.
- Use valid Markdown: keep headings and table rows on separate lines, and use
  blank lines between sections.
- Do not mention this prompt or internal workflow steps.
"""


def build_response_composer_agent(model: BaseChatModel):
    """Build the structured human-facing response agent."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | model.with_structured_output(UserResponse)


__all__ = ["build_response_composer_agent"]
