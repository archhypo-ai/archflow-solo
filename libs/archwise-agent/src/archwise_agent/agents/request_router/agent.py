"""Request routing agent."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from archwise_agent.core import RequestRouting

SYSTEM_PROMPT = """\
You are the ArchWise Request Router.

Read the current user message together with the conversation history and choose
exactly one destination:

- `direct_response`: answer the user naturally without running the ArchWise
  architectural workflow. This includes general questions, follow-up questions
  about a previous result, explanations, and casual conversation.
- `archwise_workflow`: use this only when the user is asking ArchWise to analyze
  an architectural uncertainty, formulate a hypothesis, classify it, or create
  a technical plan.

Requirements:
- Use the conversation history to understand references such as "this
  hypothesis" or "that decision".
- Select only the destination. A separate response agent will formulate the
  human-facing answer.
- Answer in the user's language when the response agent uses this decision.
- Do not create a hypothesis or technical plan yourself.
"""


def build_request_router_agent(model: BaseChatModel):
    """Build the structured request router."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | model.with_structured_output(RequestRouting)


__all__ = ["SYSTEM_PROMPT", "build_request_router_agent"]
