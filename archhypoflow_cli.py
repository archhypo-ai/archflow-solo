#!/usr/bin/env python3
"""Run one ArchHypo Flow request without starting the HTTP server.

Examples (from the repository root)::

    uv run --project libs/archhypo-flow-agent python archhypoflow_cli.py \
        "Can one server handle the projected load?"
    uv run --project libs/archhypo-flow-agent python archhypoflow_cli.py input.txt
    cat input.txt | uv run --project libs/archhypo-flow-agent python \
        archhypoflow_cli.py -
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4

REPOSITORY_ROOT = Path(__file__).resolve().parent
AGENT_PROJECT_ROOT = REPOSITORY_ROOT / "libs" / "archhypo-flow-agent"


def _load_environment() -> None:
    """Load the package's .env while preserving already-exported variables."""

    from dotenv import load_dotenv

    current_directory_env = Path.cwd() / ".env"
    package_env = AGENT_PROJECT_ROOT / ".env"
    if current_directory_env.is_file():
        load_dotenv(current_directory_env, override=False)
    if package_env.is_file() and package_env != current_directory_env:
        load_dotenv(package_env, override=False)


def _read_input(source: str, *, force_text: bool) -> str:
    if source == "-":
        text = sys.stdin.read()
    else:
        path = Path(source).expanduser()
        if path.exists() and not path.is_file() and not force_text:
            raise ValueError(f"Input path is not a file: {path}")
        if path.is_file() and not force_text:
            text = path.read_text(encoding="utf-8")
        else:
            text = source

    if not text.strip():
        raise ValueError("Input must not be empty")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run an ArchHypo Flow request. INPUT may be literal text, a text "
            "file, or '-' to read from stdin."
        )
    )
    parser.add_argument("input", help="Text, file path, or '-' for stdin")
    parser.add_argument(
        "--text",
        action="store_true",
        help="Treat INPUT as literal text even if it matches an existing file",
    )
    arguments = parser.parse_args()

    try:
        message = _read_input(arguments.input, force_text=arguments.text)
    except (OSError, ValueError) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2

    try:
        _load_environment()
        from archhypo_flow_agent.config import settings
        from archhypo_flow_agent.core import ChatRequest
        from archhypo_flow_agent.providers import (
            create_openrouter_model,
            create_system_one_client,
        )
        from archhypo_flow_agent.services import AgentService

        service = AgentService(
            model=create_openrouter_model(settings),
            system_one_client=create_system_one_client(settings),
        )
    except (ImportError, ValueError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2

    try:
        response = service.respond(
            ChatRequest(
                thread_id=uuid4().hex,
                message=message,
                language="pt-BR",
            )
        )
        print(response.message)
        return 0
    except Exception as error:
        print(f"ArchHypo Flow failed: {error}", file=sys.stderr)
        return 1
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
