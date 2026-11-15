from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from archhypo_flow_agent.backend.controllers.skills import router


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))


def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_open_folder_creates_application_skills_directory(tmp_path: Path):
    response = client().post("/api/skills/folder")
    assert response.status_code == 200
    assert response.json() == {"path": str(tmp_path / ".archhypoflow/skills")}
    assert (tmp_path / ".archhypoflow/skills").is_dir()


def test_create_and_list_skills_on_disk(tmp_path: Path):
    api = client()
    payload = {
        "name": "architecture-review",
        "description": "Review: architecture",
        "instructions": "# Review\nInspect the context.",
        "files": {"references/guide.md": "# Guide"},
    }
    assert api.get("/api/skills").json() == []
    response = api.post("/api/skills", json=payload)
    assert response.status_code == 201
    directory = tmp_path / ".archhypoflow/skills/architecture-review"
    content = (directory / "SKILL.md").read_text()
    assert yaml.safe_load(content.split("---", 2)[1]) == {
        "name": "architecture-review",
        "description": "Review: architecture",
    }
    assert (directory / "references/guide.md").read_text() == "# Guide"
    assert api.get("/api/skills").json() == [
        {
            "name": "architecture-review",
            "description": "Review: architecture",
            "error": "",
        }
    ]
    assert api.post("/api/skills", json=payload).status_code == 409
    assert (directory / "references/guide.md").read_text() == "# Guide"


def test_invalid_paths_and_symlinks_are_rejected(tmp_path: Path):
    api = client()
    base = {
        "name": "safe",
        "description": "desc",
        "instructions": "body",
    }
    for filename in (
        "../escape",
        "/absolute",
        "references/../../escape",
        "SKILL.md",
        "a\\b",
    ):
        assert (
            api.post("/api/skills", json={**base, "files": {filename: "x"}}).status_code
            == 422
        )
    assert not (tmp_path / ".archhypoflow").exists()
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / ".archhypoflow").symlink_to(outside, target_is_directory=True)
    assert api.post("/api/skills", json=base).status_code == 400
    assert not (outside / "skills").exists()


def test_invalid_existing_skill_is_reported(tmp_path: Path):
    directory = tmp_path / ".archhypoflow/skills/broken"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text("no front matter")
    result = client().get("/api/skills").json()
    assert result[0]["name"] == "broken"
    assert result[0]["error"]


def test_edit_delete_and_external_change_conflict(tmp_path: Path):
    api = client()
    payload = {
        "name": "demo",
        "description": "before",
        "instructions": "first",
        "files": {"references/a.md": "old"},
    }
    assert api.post("/api/skills", json=payload).status_code == 201
    detail = api.get("/api/skills/demo").json()
    assert detail["files"]["SKILL.md"] == "first"
    assert detail["files"]["references/a.md"] == "old"
    directory = tmp_path / ".archhypoflow/skills/demo"
    updated = {
        **payload,
        "description": "after",
        "instructions": "second",
        "files": {"references/b.md": "new"},
        "revision": detail["revision"],
    }
    response = api.put("/api/skills/demo", json=updated)
    assert response.status_code == 200, response.text
    assert not (directory / "references/a.md").exists()
    assert (directory / "references/b.md").read_text() == "new"
    assert api.put("/api/skills/demo", json=updated).status_code == 409
    latest = response.json()
    (directory / "references/b.md").write_text("external")
    assert (
        api.request(
            "DELETE", "/api/skills/demo", json={"revision": latest["revision"]}
        ).status_code
        == 409
    )
    latest = api.get("/api/skills/demo").json()
    assert (
        api.request(
            "DELETE", "/api/skills/demo", json={"revision": latest["revision"]}
        ).status_code
        == 204
    )
    assert not directory.exists()


def test_large_skill_preserves_uneditable_files_and_handles_conflicts(tmp_path: Path):
    api = client()
    directory = tmp_path / ".archhypoflow/skills/large"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        "---\nname: large\ndescription: Test\n---\nInstructions"
    )
    refs = directory / "references"
    refs.mkdir()
    for index in range(80):
        (refs / f"file-{index}.md").write_text(f"reference {index}")
    (refs / "large.bin").write_bytes(b"a" * 100_001)
    (refs / "binary.bin").write_bytes(b"\x00\xff")
    detail = api.get("/api/skills/large").json()
    assert len(detail["files"]) == 81
    assert set(detail["unavailable"]) == {
        "references/large.bin",
        "references/binary.bin",
    }
    files = {key: value for key, value in detail["files"].items() if key != "SKILL.md"}
    result = api.put(
        "/api/skills/large",
        json={
            "name": "large",
            "description": "Updated",
            "instructions": "Updated",
            "files": files,
            "revision": detail["revision"],
        },
    )
    assert result.status_code == 200, result.text
    assert (refs / "large.bin").read_bytes() == b"a" * 100_001
    assert (refs / "binary.bin").read_bytes() == b"\x00\xff"
    (refs / "binary.bin").write_bytes(b"changed")
    assert (
        api.request(
            "DELETE", "/api/skills/large", json={"revision": result.json()["revision"]}
        ).status_code
        == 409
    )


def test_invalid_skill_can_be_fixed_or_deleted(tmp_path: Path):
    api = client()
    directory = tmp_path / ".archhypoflow/skills/broken"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text("instructions without front matter")
    detail = api.get("/api/skills/broken").json()
    assert detail["error"]
    assert detail["files"]["SKILL.md"] == "instructions without front matter"
    response = api.put(
        "/api/skills/broken",
        json={
            "name": "broken",
            "description": "Fixed",
            "instructions": detail["files"]["SKILL.md"],
            "revision": detail["revision"],
        },
    )
    assert response.status_code == 200, response.text
    assert not response.json()["error"]
    assert (
        api.request(
            "DELETE",
            "/api/skills/broken",
            json={"revision": response.json()["revision"]},
        ).status_code
        == 204
    )
