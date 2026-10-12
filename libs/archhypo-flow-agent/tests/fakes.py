"""Deterministic model stubs for service and API tests."""

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage


class StubChatModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def stub_chat_model(
    message: str = "Understood. Let's explore this architectural decision.",
) -> StubChatModel:
    responses = [
        AIMessage(content=message, id=f"stub-response-{index}") for index in range(100)
    ]
    return StubChatModel(responses=responses)


__all__ = ["StubChatModel", "stub_chat_model"]
