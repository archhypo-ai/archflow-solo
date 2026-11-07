"""Bounded extraction of explicitly supplied documentation bytes.

This module does not open paths or enumerate directories. The caller must obtain
the user's authorization before passing a file and must treat its text as data.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePath
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_EXTRACTED_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_CHARACTERS = 1_000_000
MAX_ARCHIVE_ENTRIES = 2_000
_WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class DocumentExtractionError(ValueError):
    """A document was rejected or could not be safely extracted."""


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    name: str
    text: str


def extract_document(filename: str, content: bytes) -> ExtractedDocument:
    """Extract text from a bounded, explicitly supplied document.

    Legacy Word files are deliberately rejected until a supported converter is
    bundled. A filename/extension is not proof that a file contains no code or
    confidential material; callers must show the selection before analysis.
    """
    name = PurePath(filename).name
    if not name or name != filename or "\\" in filename or "\x00" in filename:
        raise DocumentExtractionError("Invalid document filename.")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentExtractionError("Document exceeds the size limit.")
    extension = PurePath(name).suffix.lower()
    if extension in {".md", ".txt"}:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise DocumentExtractionError("Document must be UTF-8 text.") from error
        if "\x00" in text:
            raise DocumentExtractionError("Binary content is not accepted as text.")
    elif extension == ".docx":
        text = _extract_docx(content)
    elif extension == ".doc":
        raise DocumentExtractionError("Legacy .doc conversion is not available.")
    else:
        raise DocumentExtractionError("Unsupported document format.")
    if len(text) > MAX_DOCUMENT_CHARACTERS:
        raise DocumentExtractionError("Extracted text exceeds the size limit.")
    if not text.strip():
        raise DocumentExtractionError("Document contains no extractable text.")
    return ExtractedDocument(name=name, text=text)


def _extract_docx(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if (
                len(entries) > MAX_ARCHIVE_ENTRIES
                or sum(entry.file_size for entry in entries) > MAX_EXTRACTED_BYTES
            ):
                raise DocumentExtractionError(
                    "Word document exceeds extraction limits."
                )
            document = archive.getinfo("word/document.xml")
            if document.file_size > MAX_EXTRACTED_BYTES:
                raise DocumentExtractionError(
                    "Word document exceeds extraction limits."
                )
            root = ElementTree.fromstring(archive.read(document))
    except (BadZipFile, KeyError, ElementTree.ParseError, RuntimeError) as error:
        raise DocumentExtractionError(
            "Invalid or unreadable .docx document."
        ) from error

    paragraphs = []
    for paragraph in root.iter(f"{_WORD_NAMESPACE}p"):
        pieces: list[str] = []
        for item in paragraph.iter():
            if item.tag == f"{_WORD_NAMESPACE}t" and item.text:
                pieces.append(item.text)
            elif item.tag == f"{_WORD_NAMESPACE}tab":
                pieces.append("\t")
            elif item.tag in {f"{_WORD_NAMESPACE}br", f"{_WORD_NAMESPACE}cr"}:
                pieces.append("\n")
        paragraphs.append("".join(pieces))
    return "\n".join(paragraphs)
