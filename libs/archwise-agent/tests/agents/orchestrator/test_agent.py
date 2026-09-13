import threading
import time

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService, build_archwise_agent


def test_agent_responds_and_preserves_thread_history() -> None:
    model = FakeListChatModel(responses=["first reply", "second reply"])
    agent = AgentService(model=model, checkpointer=InMemorySaver())

    first = agent.send(thread_id="thread-1", message="hello")
    second = agent.send(thread_id="thread-1", message="follow up")

    assert first.text == "first reply"
    assert second.text == "second reply"

    state = agent.agent.get_state(
        {"configurable": {"thread_id": "thread-1"}}
    )
    assert len(state.values["messages"]) == 4


def test_agent_stream_can_be_cancelled() -> None:
    service = AgentService(
        model=FakeListChatModel(responses=["a" * 40], sleep=0.02),
        checkpointer=InMemorySaver(),
    )
    stream = service.stream(
        thread_id="cancel-thread",
        message="hello",
        run_id="cancel-run",
    )
    assert next(stream).kind == "phase"

    events = []
    consumer = threading.Thread(target=lambda: events.extend(stream))
    consumer.start()
    time.sleep(0.05)

    assert service.cancel_run("cancel-run") is True
    consumer.join(timeout=3)

    assert not consumer.is_alive()
    assert any(event.kind == "cancelled" for event in events)
    assert not any(event.kind == "done" for event in events)


def test_build_agent_accepts_injected_model() -> None:
    agent = build_archwise_agent(
        model=FakeListChatModel(responses=["ok"]),
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "hello"}]},
        {"configurable": {"thread_id": "thread-2"}},
    )

    assert result["messages"][-1].content == "ok"
