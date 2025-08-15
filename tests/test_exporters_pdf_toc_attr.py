from pathlib import Path
from unittest import mock

from podcast_transcriber.exporters.exporter import export_transcript


def test_pdf_toc_from_segments_and_attribution(tmp_path, monkeypatch):
    out = tmp_path / "toc.pdf"
    segments = [
        {"start": 0.0, "end": 1.0, "text": "Intro"},
        {"start": 60.0, "end": 61.0, "text": "Chapter"},
    ]

    class FakePDF:
        def __init__(self, *a, **k):
            self.l_margin = 10
            self.w = 210
            self._pages = 0

        def set_auto_page_break(self, *a, **k):
            pass

        def add_page(self):
            self._pages += 1

        def set_title(self, *a, **k):
            pass

        def set_author(self, *a, **k):
            pass

        def set_font(self, *a, **k):
            pass

        def cell(self, *a, **k):
            pass

        def multi_cell(self, *a, **k):
            pass

        def ln(self, *a, **k):
            pass

        def output(self, path):
            Path(path).write_bytes(b"%PDF-1.4\n...")

        def image(self, *a, **k):
            pass

    import sys

    sys.modules["fpdf"] = mock.MagicMock(FPDF=FakePDF)

    export_transcript(
        "Hello\n\nWorld",
        str(out),
        "pdf",
        title="T",
        author="A",
        segments=segments,
        auto_toc=True,
        pdf_append_attribution=True,
        pdf_attribution_text="Data license...",
    )
    assert out.exists() and out.stat().st_size > 0
