from pathlib import Path

import pytest

from archhypo_flow_agent.persistence.paths import _storage_root


def test_default_storage_root_is_shared_with_application_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("ARCHHYPO_FLOW_STORAGE_ROOT", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    assert _storage_root() == tmp_path / ".archhypoflow"


def test_explicit_storage_root_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("ARCHHYPO_FLOW_STORAGE_ROOT", "~/custom-storage")
    assert _storage_root() == tmp_path / "custom-storage"
