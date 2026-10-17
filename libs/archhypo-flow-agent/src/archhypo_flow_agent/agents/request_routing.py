"""Structured LLM fallback for classifying the user's request intent."""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from archhypo_flow_agent.core import RequestRouting

SYSTEM_PROMPT = """\
You are the ArchHypo Flow request router.

Classify the latest user request using the full conversation and the supplied
structured analysis state. Select exactly one intent:

- `new_uncertainty`: the user introduces a software-architecture uncertainty
  in a concrete system and asks to identify, classify, assess, validate, compare,
  or decide about it. This includes asking for the central quality domain of a
  concrete scenario that contains unresolved design decisions. Do not require
  the literal words "uncertainty", "hypothesis", or "ArchHypo".
- `alternative_hypothesis`: the user asks for another hypothesis about the
  currently active uncertainty. Preserve the previous hypothesis as a separate
  result; do not treat this as a new uncertainty.
- `revise_hypothesis`: the user explicitly asks to revise or reformulate the
  currently active hypothesis. The prior version remains part of the history.
- `contextual_question`: a question or follow-up about software architecture,
  ArchHypo, the conversation, or an existing result; answer without starting a
  new ArchHypo workflow. Use this for conceptual explanations and taxonomy-only
  questions without a concrete system or unresolved architectural decision.
- `out_of_scope`: a request outside software architecture and engineering.
- `clarification`: the target or intent is ambiguous. Ask one short question
  rather than guessing or combining independent uncertainties.

General software-architecture questions are in scope for a direct answer and do
not automatically require the ArchHypo workflow. However, a concrete project
scenario with an unresolved decision remains an ArchHypo request even when the
user asks only to classify or assess its central concern. For example, "classify
the central domain" followed by a capacity question such as whether one server
can handle projected peak throughput is `new_uncertainty`, not a direct answer.
Do not route directly based only on a wrapper's verb (such as "classify" or
"summarize"); inspect the concrete system scenario it contains.
If the user explicitly asks for the central concern among several topics, route
to discovery, which must select one concern rather than combine them. If no
central concern or priority can be inferred, choose `clarification`.

A mere mention of an already-understood uncertainty is not enough by itself;
distinguish requests to explain an existing result from requests to investigate
an unresolved decision. Never formulate a hypothesis or plan in this routing
decision.
"""

REQUEST_INTENT_CRITERIA = {
    "new_uncertainty": (
        "A concrete software system/project has an unresolved architectural "
        "decision or behavior. Route here when asked to identify, classify, "
        "assess, validate, compare, or decide about it, even if the user does "
        "not say 'hypothesis' or 'ArchHypo'. This includes a narrative asking "
        "for the central quality domain when it contains a measurable capacity "
        "question, compatibility uncertainty, or another concrete design "
        "decision (for example, whether one server can sustain projected peak "
        "throughput). If the user asks for the central concern among several "
        "topics, send the message to discovery to select one; do not merge "
        "independent concerns."
    ),
    "alternative_hypothesis": (
        "The user asks for another hypothesis about the active uncertainty. "
        "Preserve prior results and do not start discovery again."
    ),
    "revise_hypothesis": (
        "The user explicitly asks to revise the active hypothesis. Preserve "
        "the previous completed result."
    ),
    "contextual_question": (
        "A conceptual/general explanation, a question about the conversation "
        "or a completed result, or a taxonomy-only classification without a "
        "concrete system and unresolved decision. Do not start ArchHypo."
    ),
    "out_of_scope": (
        "The request is outside software architecture and software engineering."
    ),
    "clarification": (
        "The intended target is ambiguous, or independent concerns are "
        "presented without a requested or inferable central concern. Ask a "
        "short clarifying question instead of combining them."
    ),
}

SYSTEM_ONE_ROUTING_QUESTION = {
    "type": "choice",
    "instructions": (
        "Classify the latest user request using the full conversation and "
        "structured analysis state. Choose exactly one intent. A request to "
        "classify a concrete project scenario can still require ArchHypo when "
        "the scenario contains an unresolved architectural decision. Inspect "
        "the scenario, not only the wrapper's wording."
    ),
    "criteria": REQUEST_INTENT_CRITERIA,
}


def build_request_routing_agent(model: BaseChatModel):
    """Build a structured request router used when SystemOne is unavailable."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}\n\n{analysis_context}"),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | model.with_structured_output(RequestRouting)


__all__ = [
    "REQUEST_INTENT_CRITERIA",
    "SYSTEM_ONE_ROUTING_QUESTION",
    "SYSTEM_PROMPT",
    "build_request_routing_agent",
]
