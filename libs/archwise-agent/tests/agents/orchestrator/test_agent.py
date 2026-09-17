import threading
import time

from langgraph.checkpoint.memory import InMemorySaver

from archwise_agent import AgentService, Hypothesis, build_archwise_agent
from tests.fakes import archhypo_json, fake_hypothesis_model


def test_agent_runs_one_uncertainty_at_a_time() -> None:
    model = fake_hypothesis_model(["first reply", "second reply"])
    agent = AgentService(model=model, checkpointer=InMemorySaver())

    first = agent.send(thread_id="thread-1", message="hello")
    second = agent.send(thread_id="thread-1", message="follow up")

    assert first.result.hypothesis == Hypothesis(
        title="Hypothesis 1",
        statement="first reply",
        justification="Derived from the supplied uncertainty.",
    )
    assert first.text == archhypo_json("hello", "first reply")
    assert second.text == archhypo_json(
        "follow up",
        "second reply",
        index=2,
    )

    state = agent.agent.get_state(
        {"configurable": {"thread_id": "thread-1"}}
    )
    assert state.values["uncertainty"] == "follow up"
    assert state.values["result"].hypothesis.statement == "second reply"


def test_agent_stream_can_be_cancelled() -> None:
    service = AgentService(
        model=fake_hypothesis_model(["a" * 40], sleep=0.2),
        checkpointer=InMemorySaver(),
    )
    stream = service.stream(
        thread_id="cancel-thread",
        message="hello",
        run_id="cancel-run",
    )
    assert next(stream).type == "phase"

    events = []
    consumer = threading.Thread(target=lambda: events.extend(stream))
    consumer.start()
    time.sleep(0.05)

    assert service.cancel_run("cancel-run") is True
    consumer.join(timeout=3)

    assert not consumer.is_alive()
    assert any(event.type == "cancelled" for event in events)
    assert not any(event.type == "done" for event in events)


def test_build_agent_accepts_injected_model() -> None:
    agent = build_archwise_agent(
        model=fake_hypothesis_model(["ok"]),
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"uncertainty": "hello"},
        {"configurable": {"thread_id": "thread-2"}},
    )

    assert result["result"].hypothesis.statement == "ok"
    assert result["result"].uncertainty == "hello"
