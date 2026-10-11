"""Executable entry point for the ArchWise backend."""

from __future__ import annotations

import os

from .app import app


def main() -> None:
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("ARCHWISE_HOST", "127.0.0.1"),
        port=int(os.getenv("ARCHWISE_PORT", "8765")),
        log_level=os.getenv("ARCHWISE_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
