"""Errors shared by graph execution and the API boundary."""


class StructuredOutputError(RuntimeError):
    """A model stage failed schema validation after its correction attempt."""

    def __init__(self, *, stage: str, attempts: int) -> None:
        self.stage = stage
        self.attempts = attempts
        super().__init__(
            f"Structured output for {stage} remained invalid after {attempts} attempts."
        )


__all__ = ["StructuredOutputError"]
