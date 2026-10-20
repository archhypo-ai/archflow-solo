"""Keep approval-dependent tests independent of the developer's local .env."""

import pytest

from archhypo_flow_agent.config import settings


@pytest.fixture(autouse=True)
def enable_human_review(monkeypatch) -> None:
    monkeypatch.setattr(settings, "hitl_enabled", True)
