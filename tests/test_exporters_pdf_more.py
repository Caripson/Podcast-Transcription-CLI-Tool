from pathlib import Path
from unittest import mock

from podcast_transcriber.exporters.exporter import export_transcript


def test_pdf_custom_font_and_header_footer(tmp_path, monkeypatch):
    out = tmp_path / "h.pdf"
    font = tmp_path / "f.ttf"
    font.write_bytes(b"TTF")

    calls = {"add_font": []}

    class FakePDF:
        def __init__(self, *args, **kwargs):
            self.l_margin = 10
            self.w = 210

        def set_auto_page_break(self, auto=True, margin=15):
            pass

        def add_page(self):
            pass

        def set_title(self, t):
            pass

        def set_author(self, a):
            pass

        def set_font(self, *args, **kwargs):
            pass

        def add_font(self, family, style, path, uni=False):
            calls["add_font"].append((family, style, Path(path).name, uni))

        def multi_cell(self, *args, **kwargs):
            pass

        def ln(self, *args, **kwargs):
            pass

        def output(self, path):
            Path(path).write_bytes(b"%PDF-1.4\n...")

        def image(self, *args, **kwargs):
            pass

    import sys

    sys.modules["fpdf"] = mock.MagicMock(FPDF=FakePDF)

    export_transcript(
        "hello",
        str(out),
        "pdf",
        title="T",
        author="A",
        pdf_font_file=str(font),
        pdf_header="Head",
        pdf_footer="Foot",
    )
    assert out.exists()
    assert calls["add_font"]
    assert calls["add_font"][0][0] == "Embedded"


def test_pdf_font_file_missing_raises(tmp_path, monkeypatch):
    out = tmp_path / "x.pdf"

    class FakePDF:
        def __init__(self, *args, **kwargs):
            pass

        def set_auto_page_break(self, *a, **k):
            pass

        def add_page(self):
            pass

        def set_title(self, *a, **k):
            pass

        def set_author(self, *a, **k):
            pass

        def set_font(self, *a, **k):
            pass

        def multi_cell(self, *a, **k):
            pass

        def ln(self, *a, **k):
            pass

        def output(self, path):
            Path(path).write_bytes(b"%PDF-1.4\n...")

    import sys

    sys.modules["fpdf"] = mock.MagicMock(FPDF=FakePDF)

    try:
        export_transcript("hi", str(out), "pdf", pdf_font_file=str(tmp_path / "missing.ttf"))
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
