"""Execute ReAct chat turns and stream their visible progress."""

import base64
import binascii
import json
from collections.abc import Iterator
from threading import Lock
from typing import Any, cast
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.types import Command
from langsmith import tracing_context

from archhypo_flow_agent.core import ChatRequest, ChatResponse, Hypothesis
from archhypo_flow_agent.observability import Observability

from .chat_context import ChatContextResolver
from .chat_projection import (
    message_text,
    messages_from_update,
    stream_event_data,
    title_from_message,
    tool_calls_from_messages,
    tool_result_value,
)
from .document_extraction import DocumentExtractionError, extract_document


class ReviewStateError(ValueError):
    """Raised when a review decision does not match the graph checkpoint."""


class ChatExecutionService:
    """Run one graph turn while serializing access to shared persistence."""

    def __init__(
        self,
        graph: Any,
        context_resolver: ChatContextResolver,
        lock: Lock,
        observability: Observability,
    ) -> None:
        self._graph = graph
        self._context_resolver = context_resolver
        self._lock = lock
        self._observability = observability

    def replace_graph(self, graph: Any) -> None:
        """Replace the graph while the owning service holds the shared lock."""
        self._graph = graph

    def respond(self, request: ChatRequest) -> ChatResponse:
        # Explicit callbacks own tracing, even when environment auto-tracing is set.
        with self._lock, tracing_context(enabled=False):
            metadata, run_context = self._context_resolver.resolve(request)
            config = self._graph_config(
                request,
                project_id=metadata.project_id if metadata else request.project_id,
                run_id=uuid4().hex,
            )
            previous_messages = self._messages_from_state(config)
            pending = self._pending_review(config)
            graph_input = self._graph_input_for_request(request, pending)
            if graph_input is None:
                self._persist_user_message(request, config)
                graph_input = {}
            result = self._graph.invoke(
                graph_input,
                config=config,
                context=run_context,
            )
            pending = self._pending_review(config)
            if pending is not None:
                _, payload = pending
                kind = payload.get("kind")
                if kind == "hypothesis_review":
                    hypothesis = _hypothesis_from_payload(payload)
                    return ChatResponse(
                        thread_id=request.thread_id,
                        title=(
                            metadata.title
                            if metadata
                            else title_from_message(request.message)
                        ),
                        message=f"Review the proposed hypothesis: {hypothesis.title}",
                        pending_hypothesis_review=hypothesis,
                    )
                return ChatResponse(
                    thread_id=request.thread_id,
                    title=(
                        metadata.title
                        if metadata
                        else title_from_message(request.message)
                    ),
                    message=_review_prompt(request.language, str(kind)),
                    pending_technical_plan_review=payload,
                )
            messages = result.get("messages", [])
            if not messages:
                raise RuntimeError("The chat graph returned no messages")

            turn_messages = messages[len(previous_messages) :]
            last_message = cast(BaseMessage, messages[-1])
            return ChatResponse(
                thread_id=request.thread_id,
                title=(
                    metadata.title if metadata else title_from_message(request.message)
                ),
                message=message_text(last_message),
                tool_calls=tool_calls_from_messages(turn_messages),
            )

    def stream(
        self,
        request: ChatRequest,
        *,
        run_id: str | None = None,
    ) -> Iterator[dict[str, object]]:
        active_run_id = run_id or uuid4().hex
        with self._lock, tracing_context(enabled=False):
            metadata, run_context = self._context_resolver.resolve(request)
            config = self._graph_config(
                request,
                project_id=metadata.project_id if metadata else request.project_id,
                run_id=active_run_id,
            )
            previous_tool_ids = {
                call.id
                for call in tool_calls_from_messages(self._messages_from_state(config))
            }
            pending = self._pending_review(config)
            graph_input = self._graph_input_for_request(request, pending)
            if graph_input is None:
                self._persist_user_message(request, config)
                graph_input = {}
            yield stream_event_data(
                active_run_id,
                request.thread_id,
                "conversation_started",
                title=(
                    metadata.title if metadata else title_from_message(request.message)
                ),
                user_message=request.message
                or (", ".join(item.name for item in request.attachments)),
                project_id=(metadata.project_id if metadata else request.project_id),
            )
            yield stream_event_data(
                active_run_id,
                request.thread_id,
                "phase",
                phase="thinking",
            )
            emitted_calls = set(previous_tool_ids)
            emitted_results = set(previous_tool_ids)
            pending_calls: set[str] = set()

            for namespace, mode, update in self._graph.stream(
                graph_input,
                config=config,
                context=run_context,
                stream_mode=["updates"],
                subgraphs=True,
            ):
                if mode != "updates":
                    continue
                if any(
                    str(part).startswith("documentary_research:") for part in namespace
                ):
                    continue
                yield from self._tool_events_from_update(
                    update,
                    run_id=active_run_id,
                    thread_id=request.thread_id,
                    emitted_calls=emitted_calls,
                    emitted_results=emitted_results,
                    pending_calls=pending_calls,
                )

            review_interrupt = self._pending_review(config)
            if review_interrupt is not None:
                interrupt_id, payload = review_interrupt
                yield stream_event_data(
                    active_run_id,
                    request.thread_id,
                    "interrupt",
                    interrupt_id=interrupt_id,
                    message=_review_prompt(
                        request.language,
                        str(payload.get("kind", "")),
                    ),
                    payload=payload,
                )
                return

            messages = self._messages_from_state(config)
            if not messages:
                raise RuntimeError("The chat graph returned no messages")
            message = message_text(cast(BaseMessage, messages[-1]))
            if not message:
                raise RuntimeError("The chat graph returned an empty reply")

            yield stream_event_data(
                active_run_id,
                request.thread_id,
                "phase",
                phase="answering",
            )
            yield stream_event_data(
                active_run_id,
                request.thread_id,
                "text_delta",
                text=message,
            )
            yield stream_event_data(
                active_run_id,
                request.thread_id,
                "done",
                status="completed",
                title=(
                    metadata.title if metadata else title_from_message(request.message)
                ),
                message=message,
            )

    def _graph_config(
        self,
        request: ChatRequest,
        *,
        project_id: str | None,
        run_id: str,
    ) -> dict[str, object]:
        config = self._observability.graph_config(
            thread_id=request.thread_id,
            run_id=run_id,
            project_id=project_id,
        )
        config["configurable"] = {"thread_id": request.thread_id}
        return config

    def _persist_user_message(
        self,
        request: ChatRequest,
        config: dict[str, object],
    ) -> None:
        documents = []
        total = 0
        for attachment in request.attachments:
            try:
                data = base64.b64decode(attachment.data, validate=True)
            except (ValueError, binascii.Error) as error:
                raise DocumentExtractionError("Invalid attachment encoding.") from error
            total += len(data)
            if total > 20 * 1024 * 1024:
                raise DocumentExtractionError(
                    "Attachments exceed the total size limit."
                )
            document = extract_document(attachment.name, data)
            item = {
                "name": document.name,
                "text": document.text,
                "size_bytes": len(data),
            }
            if attachment.folder_id is not None and attachment.folder_name is not None:
                item.update(
                    folder_id=attachment.folder_id, folder_name=attachment.folder_name
                )
            documents.append(item)
        text = request.message.strip()
        if not text and documents:
            text = (
                "Analise os documentos anexados."
                if request.language == "pt-BR"
                else "Analyze the attached documents."
            )
        self._graph.update_state(
            config,
            {
                "messages": [
                    HumanMessage(
                        content=text,
                        additional_kwargs={
                            "document_attachments": documents,
                        }
                        if documents
                        else {},
                    )
                ]
            },
            as_node="__start__",
        )

    def _messages_from_state(self, config: dict[str, object]) -> list[BaseMessage]:
        state = self._graph.get_state(config)
        values = state.values if isinstance(state.values, dict) else {}
        raw_messages = values.get("messages", [])
        return [message for message in raw_messages if isinstance(message, BaseMessage)]

    def _pending_review(
        self,
        config: dict[str, object],
    ) -> tuple[str, dict[str, object]] | None:
        snapshot = self._graph.get_state(config)
        for task in getattr(snapshot, "tasks", ()):
            for pending_interrupt in task.interrupts:
                payload = pending_interrupt.value
                if isinstance(payload, dict) and payload.get("kind") in {
                    "hypothesis_review",
                    "technical_plan_review",
                }:
                    return pending_interrupt.id, payload
        return None

    def _graph_input_for_request(
        self,
        request: ChatRequest,
        pending: tuple[str, dict[str, object]] | None,
    ) -> dict[str, object] | Command | None:
        decision = request.hypothesis_review or request.technical_plan_review
        if pending is None:
            if decision is not None:
                raise ReviewStateError("There is no pending human review.")
            return None

        if request.hypothesis_review is not None:
            expected_kind = "hypothesis_review"
            decision = request.hypothesis_review
        elif request.technical_plan_review is not None:
            expected_kind = "technical_plan_review"
            decision = request.technical_plan_review
        else:
            raise ReviewStateError(
                "Approve or reject the pending review before continuing."
            )

        if pending[1].get("kind") != expected_kind:
            raise ReviewStateError("The decision does not match the pending review.")

        return Command(resume=decision.model_dump(mode="json"))

    def _tool_events_from_update(
        self,
        update: object,
        *,
        run_id: str,
        thread_id: str,
        emitted_calls: set[str],
        emitted_results: set[str],
        pending_calls: set[str],
    ) -> Iterator[dict[str, object]]:
        for message in messages_from_update(update):
            if message.type == "ai":
                for index, call in enumerate(getattr(message, "tool_calls", [])):
                    call_id = str(call.get("id") or f"tool-call-{index}")
                    if call_id in emitted_calls:
                        continue
                    emitted_calls.add(call_id)
                    pending_calls.add(call_id)
                    yield stream_event_data(
                        run_id,
                        thread_id,
                        "tool_call_start",
                        tool_call_id=call_id,
                        name=str(call.get("name") or "unknown_tool"),
                    )
                    args = call.get("args")
                    yield stream_event_data(
                        run_id,
                        thread_id,
                        "tool_call_delta",
                        tool_call_id=call_id,
                        text=json.dumps(
                            args if isinstance(args, dict) else {},
                            ensure_ascii=False,
                            default=str,
                        ),
                    )
            elif message.type == "tool":
                call_id = str(getattr(message, "tool_call_id", ""))
                if not call_id or call_id in emitted_results:
                    continue
                emitted_results.add(call_id)
                pending_calls.discard(call_id)
                yield stream_event_data(
                    run_id,
                    thread_id,
                    "tool_result",
                    tool_call_id=call_id,
                    output=tool_result_value(message.content),
                    is_error=getattr(message, "status", "success") == "error",
                )
                if not pending_calls:
                    yield stream_event_data(
                        run_id,
                        thread_id,
                        "phase",
                        phase="thinking",
                    )


def _hypothesis_from_payload(payload: dict[str, object]) -> Hypothesis:
    value = payload.get("hypothesis")
    if not isinstance(value, dict):
        raise RuntimeError("The pending hypothesis review has no hypothesis payload")
    return Hypothesis.model_validate(value)


def _review_prompt(language: str, kind: str) -> str:
    if kind == "technical_plan_review":
        if language == "pt-BR":
            return "Revise a avaliação e o plano técnico antes de concluir."
        return (
            "Review the assessment and technical plan before completing the workflow."
        )
    if language == "pt-BR":
        return "Revise a hipótese proposta antes de continuar."
    return "Review the proposed hypothesis before continuing."


__all__ = ["ChatExecutionService"]
