"""Persistence adapters and local storage paths for ArchWise."""

from .checkpoints import (
    SQLitePersistence,
    TransactionalSqliteSaver,
    open_sqlite_checkpointer,
    open_sqlite_persistence,
)
from .conversations import (
    DEFAULT_CONVERSATION_TITLE,
    ConversationMetadata,
    ConversationRepository,
    SQLiteConversationRepository,
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
    "ConversationMetadata",
    "ConversationRepository",
    "CURRENT_SCHEMA_VERSION",
    "DEFAULT_CONVERSATION_TITLE",
    "RUNTIME_ROOT",
    "SQLiteConversationRepository",
    "SQLitePersistence",
    "STORAGE_ROOT",
    "TransactionalSqliteSaver",
    "migrate_connection",
    "migrate_database",
    "open_sqlite_checkpointer",
    "open_sqlite_persistence",
]
