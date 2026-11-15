"""Application-wide skill gallery; the filesystem is the source of truth."""

import hashlib
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/skills", tags=["skills"])
_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=1024)
    instructions: str = Field(min_length=1, max_length=100_000)
    files: dict[str, str] = Field(default_factory=dict, max_length=2000)


class SkillUpdate(SkillCreate):
    revision: str = Field(min_length=64, max_length=64)


class SkillDelete(BaseModel):
    revision: str = Field(min_length=64, max_length=64)


def _root(*, create: bool = False) -> Path:
    application_directory = Path.home() / ".archhypoflow"
    directory = application_directory / "skills"
    for part in (application_directory, directory):
        if part.is_symlink():
            raise HTTPException(400, "Skill directories cannot be symbolic links")
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def _metadata(path: Path) -> dict[str, str]:
    try:
        if path.is_symlink() or path.stat().st_size > 150_000:
            raise ValueError("Invalid SKILL.md")
        content = path.read_text(encoding="utf-8")
        match = re.match(
            r"\A---[ \t]*\r?\n(.*?)^---[ \t]*\r?\n(.*)\Z", content, re.S | re.M
        )
        if not match:
            raise ValueError("Missing YAML front matter")
        data = yaml.safe_load(match.group(1))
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("name"), str)
            or not isinstance(data.get("description"), str)
        ):
            raise ValueError("Missing name or description")
        if (
            not _NAME.fullmatch(data["name"])
            or data["name"] != path.parent.name
            or not data["description"].strip()
            or not match.group(2).strip()
        ):
            raise ValueError("Invalid name, description or instructions")
        return {"name": data["name"], "description": data["description"], "error": ""}
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        return {"name": path.parent.name, "description": "", "error": str(error)}


@router.post("/folder")
def ensure_skills_folder() -> dict[str, str]:
    try:
        path = _root(create=True)
    except OSError as error:
        raise HTTPException(500, "Could not create the skills folder") from error
    return {"path": str(path)}


@router.get("")
def list_skills() -> list[dict[str, str]]:
    root = _root()
    if not root.exists():
        return []
    if not root.is_dir():
        raise HTTPException(400, "Skills path is not a directory")
    return [
        _metadata(item / "SKILL.md")
        for item in sorted(root.iterdir())
        if item.is_dir() and not item.is_symlink()
    ]


def _validated_files(payload: SkillCreate) -> list[tuple[PurePosixPath, str]]:
    name = payload.name.strip()
    description = payload.description.strip()
    if not _NAME.fullmatch(name) or not description or not payload.instructions.strip():
        raise HTTPException(
            422,
            "Name must be lowercase kebab-case; "
            "description and instructions are required",
        )
    paths: list[tuple[PurePosixPath, str]] = []
    for filename, content in payload.files.items():
        path = PurePosixPath(filename)
        if (
            not filename
            or "\\" in filename
            or path.is_absolute()
            or any(
                part in {".", ".."} or part.startswith(".")
                for part in filename.split("/")
            )
            or path.as_posix() != filename
            or filename.lower() == "skill.md"
            or len(filename) > 240
            or len(content) > 100_000
        ):
            raise HTTPException(422, f"Invalid file path or content: {filename}")
        paths.append((path, content))
    return paths


@router.post("", status_code=201)
def create_skill(payload: SkillCreate) -> dict[str, str]:
    paths = _validated_files(payload)
    name = payload.name.strip()
    description = payload.description.strip()
    root = _root(create=True)
    target = root / name
    try:
        target.mkdir()
    except FileExistsError as error:
        raise HTTPException(409, "A skill with this name already exists") from error
    try:
        frontmatter = yaml.safe_dump(
            {"name": name, "description": description},
            allow_unicode=True,
            sort_keys=False,
        )
        (target / "SKILL.md").write_text(
            f"---\n{frontmatter}---\n\n{payload.instructions.strip()}\n",
            encoding="utf-8",
        )
        for path, content in paths:
            destination = target.joinpath(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
    except (OSError, ValueError) as error:
        shutil.rmtree(target)
        raise HTTPException(400, "Could not write skill files") from error
    return _metadata(target / "SKILL.md")


def _skill_path(name: str) -> Path:
    if len(name) > 64 or not _NAME.fullmatch(name):
        raise HTTPException(404, "Skill not found")
    path = _root() / name
    if path.is_symlink() or not path.is_dir():
        raise HTTPException(404, "Skill not found")
    return path


def _snapshot(path: Path) -> tuple[dict[str, str], str, list[str]]:
    files: dict[str, str] = {}
    unavailable: list[str] = []
    digest = hashlib.sha256()
    try:
        for item in sorted(path.rglob("*")):
            relative = item.relative_to(path).as_posix()
            if item.is_symlink():
                digest.update(f"link:{relative}\0{item.readlink()}\0".encode())
                unavailable.append(relative)
                continue
            if item.is_dir():
                digest.update(f"dir:{relative}\0".encode())
                continue
            if not item.is_file():
                raise ValueError(f"Unsupported filesystem entry: {relative}")
            size = item.stat().st_size
            digest.update(f"file:{relative}\0{size}\0".encode())
            chunks = []
            with item.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    if size <= 100_000:
                        chunks.append(chunk)
            if (
                size > 100_000
                or len(files) >= 2000
                or len(relative) > 240
                or "\\" in relative
                or any(part.startswith(".") for part in relative.split("/"))
            ):
                unavailable.append(relative)
                continue
            try:
                text = b"".join(chunks).decode("utf-8")
                if "\0" in text:
                    raise ValueError("Binary file")
                files[relative] = text
            except (UnicodeError, ValueError):
                unavailable.append(relative)
    except (OSError, ValueError) as error:
        raise HTTPException(422, f"Cannot read this skill: {error}") from error
    return files, digest.hexdigest(), unavailable


@router.get("/{name}")
def get_skill(name: str) -> dict[str, object]:
    path = _skill_path(name)
    metadata = _metadata(path / "SKILL.md")
    files, revision, unavailable = _snapshot(path)
    content = files.get("SKILL.md", "")
    match = re.match(
        r"\A---[ \t]*\r?\n(.*?)^---[ \t]*\r?\n(.*)\Z", content, re.S | re.M
    )
    files["SKILL.md"] = match.group(2).strip() if match else content
    return {
        **metadata,
        "files": files,
        "revision": revision,
        "unavailable": unavailable,
    }


@router.put("/{name}")
def update_skill(name: str, payload: SkillUpdate) -> dict[str, object]:
    if payload.name != name:
        raise HTTPException(422, "Renaming a skill is not supported")
    paths = _validated_files(payload)
    target = _skill_path(name)
    old_files, revision, unavailable = _snapshot(target)
    if "SKILL.md" in unavailable:
        raise HTTPException(422, "SKILL.md is too large or not a UTF-8 file")
    if revision != payload.revision:
        raise HTTPException(409, "Skill changed on disk; reload before saving")
    match = re.match(
        r"\A---[ \t]*\r?\n(.*?)^---[ \t]*\r?\n(.*)\Z",
        old_files.get("SKILL.md", ""),
        re.S | re.M,
    )
    try:
        try:
            metadata = yaml.safe_load(match.group(1)) if match else {}
        except yaml.YAMLError:
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        metadata.update(name=name, description=payload.description.strip())
        root = _root()
        with tempfile.TemporaryDirectory(prefix=".skill-edit-", dir=root) as temporary:
            temp = Path(temporary)
            staged = temp / "new"
            shutil.copytree(target, staged, symlinks=True)
            for old in old_files:
                if old != "SKILL.md" and old not in payload.files:
                    (staged / old).unlink()
            frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
            (staged / "SKILL.md").write_text(
                f"---\n{frontmatter}---\n\n{payload.instructions.strip()}\n",
                encoding="utf-8",
            )
            for relative, content in paths:
                destination = staged.joinpath(*relative.parts)
                if relative.as_posix() in unavailable or any(
                    part.is_symlink()
                    for part in (destination, *destination.parents)
                    if part != staged.parent
                ):
                    raise HTTPException(
                        422, "Cannot overwrite an unsupported file or symbolic link"
                    )
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content, encoding="utf-8")
            if _snapshot(target)[1] != revision:
                raise HTTPException(409, "Skill changed on disk; reload before saving")
            backup = temp / "previous"
            target.rename(backup)
            try:
                staged.rename(target)
            except OSError:
                backup.rename(target)
                raise
    except (OSError, ValueError, yaml.YAMLError) as error:
        raise HTTPException(400, f"Could not update skill: {error}") from error
    return get_skill(name)


@router.delete("/{name}", status_code=204)
def delete_skill(name: str, payload: SkillDelete) -> None:
    target = _skill_path(name)
    if _snapshot(target)[1] != payload.revision:
        raise HTTPException(409, "Skill changed on disk; reload before deleting")
    try:
        shutil.rmtree(target)
    except OSError as error:
        raise HTTPException(400, "Could not delete skill") from error
