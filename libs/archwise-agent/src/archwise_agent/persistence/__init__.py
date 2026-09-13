"""Persistence adapters and local storage paths for ArchWise."""

from .checkpoints import open_sqlite_checkpointer
from .conversations import (
    ConversationCatalog,
    ConversationMetadata,
    DEFAULT_CONVERSATION_TITLE,
)
from .migrations import CURRENT_SCHEMA_VERSION, migrate_connection, migrate_database
from .paths import (
    APPLICATION_ROOT,
    CHECKPOINT_DB_PATH,
    RUNTIME_ROOT,
    STORAGE_ROOT,
)

__all__ = [
    "APPLICATION_ROOT",
    "CHECKPOINT_DB_PATH",
    "ConversationCatalog",
    "ConversationMetadata",
    "CURRENT_SCHEMA_VERSION",
    "DEFAULT_CONVERSATION_TITLE",
    "RUNTIME_ROOT",
    "STORAGE_ROOT",
    "migrate_connection",
    "migrate_database",
    "open_sqlite_checkpointer",
]
