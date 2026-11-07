from io import BytesIO
from zipfile import ZipFile

import pytest

from archhypo_flow_agent.services.document_extraction import (
    MAX_DOCUMENT_BYTES,
    DocumentExtractionError,
    extract_document,
)


def docx_with(xml: str) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return output.getvalue()


def test_extracts_utf8_markdown():
    document = extract_document("adr.md", "# Decisão\nContexto".encode())
    assert document.name == "adr.md"
    assert document.text == "# Decisão\nContexto"


def test_extracts_docx_paragraphs():
    data = docx_with(
        '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Decision'
        "</w:t></w:r></w:p><w:p><w:r><w:t>Context</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    assert extract_document("adr.docx", data).text == "Decision\nContext"


@pytest.mark.parametrize(
    ("filename", "data"),
    [
        ("main.py", b"print('code')"),
        ("config.json", b"{}"),
        ("../outside.md", b"text"),
        ("directory\\file.md", b"text"),
        ("fake.md", b"\xff\x00"),
        ("empty.txt", b" "),
        ("corrupt.docx", b"not a zip"),
        ("legacy.doc", b"legacy"),
        ("large.md", b"a" * (MAX_DOCUMENT_BYTES + 1)),
    ],
)
def test_rejects_unsupported_unsafe_or_unreadable_input(filename, data):
    with pytest.raises(DocumentExtractionError):
        extract_document(filename, data)
