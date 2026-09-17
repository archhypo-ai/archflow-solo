"""Application service for uploaded folder contexts."""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from archwise_agent.persistence import (
    STORAGE_ROOT,
    FolderContextMetadata,
    FolderContextRepository,
)

from .contracts import FolderContext

MAX_CONTEXT_FILES = 10_000
MAX_CONTEXT_BYTES = 250 * 1024 * 1024
_CONTEXTS_ROOT = STORAGE_ROOT / "contexts"


class FolderContextService:
    """Persist and manage read-only folder snapshots for conversations."""

    def __init__(
        self,
        repository: FolderContextRepository,
        storage_root: Path = _CONTEXTS_ROOT,
    ) -> None:
        self._repository = repository
        self._storage_root = storage_root

    def get(self, thread_id: str) -> FolderContext | None:
        metadata = self._repository.get(thread_id)
        return _to_context(metadata) if metadata is not None else None

    def list(self) -> list[FolderContext]:
        return [_to_context(item) for item in self._repository.list()]

    def attach(
        self,
        *,
        thread_id: str,
        folder_name: str,
        files: Iterable[tuple[str, BinaryIO]],
    ) -> FolderContext:
        clean_folder_name = _clean_folder_name(folder_name)
        context_id = f"ctx-{uuid4()}"
        temporary_path = self._storage_root / f".{context_id}.tmp"
        final_path = self._storage_root / context_id
        file_count = 0
        total_bytes = 0

        try:
            temporary_path.mkdir(parents=True, exist_ok=False)
            for filename, source in files:
                file_count += 1
                if file_count > MAX_CONTEXT_FILES:
                    raise ValueError(
                        f"folder contains more than {MAX_CONTEXT_FILES} files"
                    )
                relative_path = _safe_relative_path(filename)
                target = temporary_path / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
                total_bytes += target.stat().st_size
                if total_bytes > MAX_CONTEXT_BYTES:
                    raise ValueError("folder exceeds the 250 MB context size limit")

            if file_count == 0:
                raise ValueError("folder must contain at least one file")

            temporary_path.rename(final_path)
            previous = self._repository.get(thread_id)
            metadata = FolderContextMetadata(
                context_id=context_id,
                thread_id=thread_id,
                folder_name=clean_folder_name,
                file_count=file_count,
                total_bytes=total_bytes,
                storage_path=str(final_path),
                created_at=datetime.now(UTC).isoformat(),
            )
            self._repository.replace(metadata)
            if previous is not None and self._is_managed_path(previous.storage_path):
                _remove_storage(previous.storage_path)
            return _to_context(metadata)
        except Exception:
            _remove_storage(str(temporary_path))
            _remove_storage(str(final_path))
            raise

    def attach_path(self, *, thread_id: str, folder_path: str) -> FolderContext:
        """Persist a local folder path without copying its contents."""

        source = _resolve_folder(folder_path)
        folder_name = _clean_folder_name(source.name)
        file_count, total_bytes = _folder_stats(source)
        context_id = f"ctx-{uuid4()}"
        previous = self._repository.get(thread_id)
        metadata = FolderContextMetadata(
            context_id=context_id,
            thread_id=thread_id,
            folder_name=folder_name,
            file_count=file_count,
            total_bytes=total_bytes,
            storage_path=str(source),
            created_at=datetime.now(UTC).isoformat(),
        )
        self._repository.replace(metadata)
        if previous is not None and self._is_managed_path(previous.storage_path):
            _remove_storage(previous.storage_path)
        return _to_context(metadata)

    def _is_managed_path(self, path: str) -> bool:
        try:
            return Path(path).resolve().is_relative_to(self._storage_root.resolve())
        except (OSError, RuntimeError):
            return False

    def delete(self, thread_id: str) -> bool:
        metadata = self._repository.delete(thread_id)
        if metadata is None:
            return False
        if self._is_managed_path(metadata.storage_path):
            _remove_storage(metadata.storage_path)
        return True


def _resolve_folder(folder_path: str) -> Path:
    if not folder_path.strip():
        raise ValueError("folder_path must not be empty")
    try:
        source = Path(folder_path).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError("selected folder is not available") from error
    if not source.is_dir():
        raise ValueError("selected path is not a folder")
    return source


def _folder_stats(folder: Path) -> tuple[int, int]:
    file_count = 0
    total_bytes = 0
    try:
        candidates = folder.rglob("*")
        for candidate in candidates:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            file_count += 1
            if file_count > MAX_CONTEXT_FILES:
                raise ValueError(f"folder contains more than {MAX_CONTEXT_FILES} files")
            total_bytes += candidate.stat().st_size
            if total_bytes > MAX_CONTEXT_BYTES:
                raise ValueError("folder exceeds the 250 MB context size limit")
    except OSError as error:
        raise ValueError("selected folder could not be inspected") from error

    if file_count == 0:
        raise ValueError("folder must contain at least one file")
    return file_count, total_bytes


def _to_context(metadata: FolderContextMetadata) -> FolderContext:
    return FolderContext(
        context_id=metadata.context_id,
        thread_id=metadata.thread_id,
        folder_name=metadata.folder_name,
        file_count=metadata.file_count,
        total_bytes=metadata.total_bytes,
    )


def _clean_folder_name(value: str) -> str:
    clean = " ".join(value.strip().split())
    if not clean:
        raise ValueError("folder_name must not be empty")
    return clean[:255]


def _safe_relative_path(filename: str) -> Path:
    normalized = filename.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or ":" in path.parts[0]
    ):
        raise ValueError("folder contains an invalid file path")
    return Path(*path.parts)


def _remove_storage(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


__all__ = [
    "FolderContextService",
    "MAX_CONTEXT_BYTES",
    "MAX_CONTEXT_FILES",
]
