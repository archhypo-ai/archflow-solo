"""Answer a documentary request using only its approved attachments."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage

from archhypo_flow_agent.core import AgentState


def route_entry(state: AgentState) -> str:
    if state.get("messages"):
        message = state["messages"][-1]
        if isinstance(message, HumanMessage) and message.additional_kwargs.get(
            "document_attachments"
        ):
            return "documentary_research"
    return "request_routing"


def create_documentary_research_node(model: BaseChatModel):
    def research(state: AgentState) -> dict[str, object]:
        from archhypo_flow_agent.agents.documentary_research import (
            build_documentary_research_agent,
        )
        from archhypo_flow_agent.services.document_extraction import ExtractedDocument

        message = state["messages"][-1]
        documents = [
            ExtractedDocument(name=item["name"], text=item["text"])
            for item in message.additional_kwargs["document_attachments"]
        ]
        agent = build_documentary_research_agent(model, documents)
        result = agent.invoke(
            {"messages": [HumanMessage(content=message.content)]},
            config={"recursion_limit": 50},
        )
        response = result["messages"][-1]
        if not isinstance(response, AIMessage) or not response.text:
            raise ValueError("Documentary agent returned no response.")
        return {"messages": [AIMessage(content=response.text)]}

    return research
