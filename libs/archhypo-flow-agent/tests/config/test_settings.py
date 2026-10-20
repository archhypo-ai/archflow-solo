import pytest
from pydantic import ValidationError

from archhypo_flow_agent.config import AgentSettings


def test_hitl_is_enabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("HITL_ENABLED", raising=False)

    assert AgentSettings(_env_file=None).hitl_enabled is True


@pytest.mark.parametrize(
    ("value", "expected"),
    [("true", True), ("false", False), ("FALSE", False), ("1", True), ("0", False)],
)
def test_hitl_is_loaded_from_dotenv(monkeypatch, tmp_path, value, expected) -> None:
    monkeypatch.delenv("HITL_ENABLED", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f"HITL_ENABLED={value}\n", encoding="utf-8")

    assert AgentSettings(_env_file=env_file).hitl_enabled is expected


def test_environment_overrides_dotenv_hitl(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("HITL_ENABLED=false\n", encoding="utf-8")
    monkeypatch.setenv("HITL_ENABLED", "true")

    assert AgentSettings(_env_file=env_file).hitl_enabled is True


def test_invalid_hitl_configuration_is_rejected(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("HITL_ENABLED", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("HITL_ENABLED=invalid\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="HITL_ENABLED"):
        AgentSettings(_env_file=env_file)
