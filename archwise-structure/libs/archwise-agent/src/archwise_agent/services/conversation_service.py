"""Application service for conversation metadata use cases."""

from __future__ import annotations

from archwise_agent.persistence import ConversationMetadata, ConversationRepository


class ConversationService:
    """Coordinate conversation metadata without exposing its storage adapter."""

    def __init__(self, repository: ConversationRepository) -> None:
        self._repository = repository

    def list(self) -> list[ConversationMetadata]:
        """List conversation metadata."""

        return self._repository.list()

    def get(self, thread_id: str) -> ConversationMetadata | None:
        """Load metadata for one thread."""

        return self._repository.get(thread_id)

    def ensure(
        self,
        thread_id: str,
        title: str | None = None,
    ) -> ConversationMetadata:
        """Create metadata if needed and update its activity timestamp."""

        return self._repository.ensure(thread_id, title)

    def update(
        self,
        thread_id: str,
        *,
        title: str | None = None,
        pinned: bool | None = None,
    ) -> ConversationMetadata | None:
        """Update conversation metadata."""

        return self._repository.update(thread_id, title=title, pinned=pinned)

    def delete(self, thread_id: str) -> bool:
        """Delete metadata for one thread."""

        return self._repository.delete(thread_id)


__all__ = ["ConversationService"]
