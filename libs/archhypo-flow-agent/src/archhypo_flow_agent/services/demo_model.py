"""Deterministic local model used until a provider is configured."""

from langchain_core.language_models.fake_chat_models import FakeListChatModel


class DemoChatModel(FakeListChatModel):
    """Keep the chat usable without API credentials while wiring persistence."""

    def __init__(self) -> None:
        super().__init__(
            responses=["Understood. Let's explore this architectural decision."]
        )

    def bind_tools(self, tools, **kwargs):
        return self

    def set_language(self, language: str) -> None:
        self.responses = [
            "Entendi. Vamos explorar essa decisão arquitetural."
            if language == "pt-BR"
            else "Understood. Let's explore this architectural decision."
        ]
        self.i = 0


__all__ = ["DemoChatModel"]
