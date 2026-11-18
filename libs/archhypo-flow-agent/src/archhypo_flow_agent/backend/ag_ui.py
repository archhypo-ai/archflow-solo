"""Expose the ArchHypo service through the AG-UI LangGraph HTTP integration."""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import closing
from typing import cast

from ag_ui.core import (
    BaseEvent,
    CustomEvent,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
from fastapi import FastAPI
from starlette.concurrency import iterate_in_threadpool

from archhypo_flow_agent.backend.controllers.chat import (
    _artifact_persistence_error_message,
    _structured_output_error_message,
)
from archhypo_flow_agent.core import ChatRequest, StructuredOutputError
from archhypo_flow_agent.persistence import ArtifactPersistenceError
from archhypo_flow_agent.services import AgentService
from archhypo_flow_agent.services.chat_execution import ReviewStateError
from archhypo_flow_agent.services.document_extraction import DocumentExtractionError

logger = logging.getLogger(__name__)


class ArchHypoAgent:
    """Implement the endpoint's agent interface without bypassing AgentService."""

    name = "archhypo-flow"

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def clone(self) -> "ArchHypoAgent":
        return ArchHypoAgent(self.app)

    async def run(self, input_data: RunAgentInput) -> AsyncIterator[BaseEvent]:
        events = self._events(input_data)
        try:
            async for event in iterate_in_threadpool(events):
                yield event
        finally:
            events.close()

    def _events(self, input_data: RunAgentInput) -> Iterator[BaseEvent]:
        run = {"thread_id": input_data.thread_id, "run_id": input_data.run_id}
        yield RunStartedEvent(**run)
        message_id = f"{input_data.run_id}:assistant"
        text_started = False
        open_tools: set[str] = set()

        def close_streams() -> Iterator[BaseEvent]:
            if text_started:
                yield TextMessageEndEvent(message_id=message_id)
            for tool_id in sorted(open_tools):
                yield ToolCallEndEvent(tool_call_id=tool_id)

        try:
            service: AgentService = self.app.state.agent_service
            problem = (
                service.runtime_configuration_error()
                if service.dynamic_provider_settings
                else self.app.state.chat_configuration_error
            )
            if problem:
                yield RunErrorEvent(message=problem)
                return
            latest_user = next(
                (message for message in reversed(input_data.messages) if message.role == "user"),
                None,
            )
            content = latest_user.content if latest_user else ""
            if not isinstance(content, str) and content is not None:
                yield RunErrorEvent(message="Send chat text as a string and files as ArchHypo attachments.")
                return
            props = input_data.forwarded_props or {}
            options = dict(props.get("archhypo", {}))
            for key in ("hypothesis_review", "technical_plan_review", "review_interrupt_id"):
                options.pop(key, None)
            if input_data.resume:
                if len(input_data.resume) != 1:
                    raise ReviewStateError("ArchHypo expects one review answer per turn.")
                entry = input_data.resume[0]
                answer = entry.payload
                if entry.status != "resolved" or not isinstance(answer, dict):
                    raise ReviewStateError("Submit a resolved interrupt with a review decision.")
                kind = answer.get("kind")
                if kind not in ("hypothesis_review", "technical_plan_review"):
                    raise ReviewStateError("Invalid review kind.")
                options[kind] = {"decision": answer.get("decision"), "reason": answer.get("reason")}
                options["review_interrupt_id"] = entry.interrupt_id
            request = ChatRequest.model_validate({
                **options,
                "thread_id": input_data.thread_id,
                "message": content or "",
            })

            with closing(service.stream(request, run_id=input_data.run_id)) as source:
                for event in source:
                    match event["type"]:
                        case "conversation_started" | "phase":
                            yield CustomEvent(name=f"archhypo.{event['type']}", value=event)
                        case "tool_call_start":
                            tool_id = str(event["tool_call_id"])
                            open_tools.add(tool_id)
                            yield ToolCallStartEvent(tool_call_id=tool_id, tool_call_name=str(event["name"]))
                        case "tool_call_delta":
                            if event["text"]:
                                yield ToolCallArgsEvent(tool_call_id=str(event["tool_call_id"]), delta=str(event["text"]))
                        case "tool_result":
                            tool_id = str(event["tool_call_id"])
                            if tool_id in open_tools:
                                open_tools.remove(tool_id)
                                yield ToolCallEndEvent(tool_call_id=tool_id)
                            yield ToolCallResultEvent(
                                message_id=f"{input_data.run_id}:tool:{tool_id}",
                                tool_call_id=tool_id,
                                content=json.dumps(event["output"], ensure_ascii=False),
                                role="tool",
                                metadata={"isError": event["is_error"]},
                            )
                        case "text_delta":
                            if event["text"]:
                                if not text_started:
                                    text_started = True
                                    yield TextMessageStartEvent(message_id=message_id, role="assistant")
                                yield TextMessageContentEvent(message_id=message_id, delta=str(event["text"]))
                        case "interrupt":
                            yield from close_streams()
                            review = event["payload"]
                            yield RunFinishedEvent(
                                **run,
                                outcome={
                                    "type": "interrupt",
                                    "interrupts": [{
                                        "id": event["interrupt_id"],
                                        "reason": review["kind"] if isinstance(review, dict) else "human_input",
                                        "message": event["message"],
                                        "metadata": {"archhypoReview": review},
                                    }],
                                },
                            )
                            return
                        case "done":
                            if not text_started and event["message"]:
                                text_started = True
                                yield TextMessageStartEvent(message_id=message_id, role="assistant")
                                yield TextMessageContentEvent(message_id=message_id, delta=str(event["message"]))
                            yield from close_streams()
                            yield RunFinishedEvent(
                                **run, outcome={"type": "success"},
                                result={"title": event["title"], "message": event["message"]},
                            )
                            return
                        case "error":
                            yield from close_streams()
                            yield RunErrorEvent(message=str(event["message"]))
                            return
            error_message = "Chat stream ended before the response was complete."
        except StructuredOutputError as error:
            error_message = _structured_output_error_message(error)
        except ArtifactPersistenceError:
            error_message = _artifact_persistence_error_message()
        except (ReviewStateError, DocumentExtractionError, LookupError) as error:
            error_message = str(error)
        except Exception:
            logger.exception("ArchHypo AG-UI run failed")
            error_message = "Chat execution failed. Check provider settings and the backend logs."
        yield from close_streams()
        yield RunErrorEvent(message=error_message)


def register_ag_ui(app: FastAPI) -> None:
    # The helper only uses clone(), run() and name; the service owns graph execution.
    add_langgraph_fastapi_endpoint(app, cast(LangGraphAgent, ArchHypoAgent(app)), "/api/chat/stream")
