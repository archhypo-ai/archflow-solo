"""Active-run coordination for the application service."""

from __future__ import annotations

from threading import RLock

from langgraph.runtime import RunControl

from archwise_agent.core import ConcurrentRunError, ExecutionContext


class RunRegistry:
    """Track active runs and coordinate cancellation with thread deletion."""

    def __init__(self, lock: RLock | None = None) -> None:
        self._lock = lock or RLock()
        self._active_runs: dict[str, RunControl] = {}
        self._run_threads: dict[str, str] = {}
        self._deleting_threads: set[str] = set()

    def register(self, context: ExecutionContext, control: RunControl) -> None:
        """Register a run before graph execution starts."""

        with self._lock:
            if context.run_id in self._active_runs:
                raise ValueError("run_id is already active")
            if any(
                active_thread_id == context.thread_id
                for active_thread_id in self._run_threads.values()
            ):
                raise ConcurrentRunError(
                    "thread_id already has an active run; wait for it to finish "
                    "or cancel it before sending another message"
                )
            self._active_runs[context.run_id] = control
            self._run_threads[context.run_id] = context.thread_id

    def unregister(self, run_id: str) -> None:
        """Remove a run that failed before execution began."""

        with self._lock:
            self._active_runs.pop(run_id, None)
            self._run_threads.pop(run_id, None)

    def finish(self, run_id: str) -> str | None:
        """Finish a run and return a thread ready for deferred deletion."""

        with self._lock:
            self._active_runs.pop(run_id, None)
            thread_id = self._run_threads.pop(run_id, None)
            if thread_id is None or thread_id not in self._deleting_threads:
                return None

            has_active_run = any(
                active_thread_id == thread_id
                for active_thread_id in self._run_threads.values()
            )
            if has_active_run:
                return None

            self._deleting_threads.discard(thread_id)
            return thread_id

    def active_run_id(self, thread_id: str) -> str | None:
        """Return the active run for a thread, if one exists."""

        with self._lock:
            for run_id, active_thread_id in reversed(self._run_threads.items()):
                if active_thread_id == thread_id:
                    return run_id
        return None

    def cancel(self, run_id: str) -> bool:
        """Request cooperative cancellation for one run."""

        with self._lock:
            control = self._active_runs.get(run_id)
            if control is None:
                return False
            control.request_drain("client_cancelled")
            return True

    def request_thread_deletion(self, thread_id: str) -> bool:
        """Cancel all runs for a thread and defer deletion until they finish."""

        with self._lock:
            controls = [
                self._active_runs[run_id]
                for run_id, active_thread_id in self._run_threads.items()
                if active_thread_id == thread_id
            ]
            if not controls:
                return False

            self._deleting_threads.add(thread_id)
            for control in controls:
                control.request_drain("conversation_deleted")
            return True

    def is_deleting(self, thread_id: str) -> bool:
        """Return whether a thread is waiting for active runs to finish."""

        with self._lock:
            return thread_id in self._deleting_threads


__all__ = ["RunRegistry"]
