from pathlib import Path
from unittest import mock

import pytest

from podcast_transcriber.exporters.exporter import export_book


def test_export_book_docx_with_cover_bytes(tmp_path, monkeypatch):
    out = tmp_path / "book.docx"

    class FakeDoc:
        def __init__(self):
            self.ops = []

        def add_heading(self, *a, **k):
            self.ops.append(("heading", a, k))

        def add_paragraph(self, *a, **k):
            self.ops.append(("para", a, k))
            return object()

        def add_picture(self, *a, **k):
            self.ops.append(("pic", a, k))

        def add_page_break(self):
            self.ops.append(("brk", (), {}))

        def save(self, path):
            Path(path).write_bytes(b"DOCX")

    sysmods = __import__("sys").modules
    sysmods["docx"] = type("M", (), {"Document": FakeDoc})
    sysmods["docx.shared"] = type("S", (), {"Inches": lambda x: x})

    chapters = [
        {"title": "Ch1", "text": "Hello"},
        {"title": "Ch2", "text": "World"},
    ]

    export_book(
        chapters,
        str(out),
        "docx",
        title="T",
        author="A",
        cover_image_bytes=b"JPEGDATA",
    )
    assert out.exists() and out.read_bytes().startswith(b"DOCX")


def test_export_book_pdf_basic(tmp_path, monkeypatch):
    out = tmp_path / "book.pdf"

    class FakePDF:
        def __init__(self):
            self.w = 210
            self.l_margin = 10

        def set_auto_page_break(self, *a, **k):
            pass

        def add_page(self):
            pass

        def set_font(self, *a, **k):
            pass

        def multi_cell(self, *a, **k):
            pass

        def ln(self, *a, **k):
            pass

        def output(self, path):
            Path(path).write_bytes(b"%PDF-1.4")

    sysmods = __import__("sys").modules
    sysmods["fpdf"] = mock.MagicMock(FPDF=FakePDF)

    chapters = [{"title": "Ch1", "text": "Hello\n\nWorld"}]
    export_book(chapters, str(out), "pdf", title="T", author="A")
    assert out.exists() and out.read_bytes().startswith(b"%PDF-1.4")


def test_export_book_md_and_txt(tmp_path):
    md_out = tmp_path / "book.md"
    txt_out = tmp_path / "book.txt"
    chapters = [{"title": "Ch1", "text": "Hello"}]

    export_book(chapters, str(md_out), "md", title="T", author="A")
    export_book(chapters, str(txt_out), "txt", title="T", author="A")
    assert "Ch1" in md_out.read_text(encoding="utf-8")
    assert "Ch1" in txt_out.read_text(encoding="utf-8")


def test_export_book_unsupported_raises(tmp_path):
    out = tmp_path / "book.xyz"
    with pytest.raises(ValueError):
        export_book([{"title": "X", "text": "Y"}], str(out), "xyz")

