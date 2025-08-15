from pathlib import Path
from unittest import mock

from podcast_transcriber.exporters.exporter import export_transcript


def test_docx_cover_first_and_footer(tmp_path, monkeypatch):
    out = tmp_path / "t.docx"
    cover = tmp_path / "c.jpg"
    cover.write_bytes(b"JPG")

    class FakeRun:
        def __init__(self):
            self._r = []

    class FakeParagraph:
        def add_run(self, text=None):  # text ignored
            return FakeRun()

    class FakeFooter:
        def __init__(self):
            self.paragraphs = []

        def add_paragraph(self):
            p = FakeParagraph()
            self.paragraphs.append(p)
            return p

    class FakeSection:
        def __init__(self):
            self.footer = FakeFooter()

    class FakeDoc:
        def __init__(self):
            self._sections = [FakeSection()]

        @property
        def sections(self):
            return self._sections

        def add_page_break(self):
            pass

        def add_paragraph(self, *args, **kwargs):
            class P:
                def add_run(self, x):
                    class R:
                        pass

                    return R()

            return P()

        def add_heading(self, *args, **kwargs):
            pass

        def add_picture(self, *args, **kwargs):
            pass

        def save(self, path):
            Path(path).write_bytes(b"DOCX")

    import sys

    # Fake required modules/classes
    sys.modules["docx"] = type("M", (), {"Document": FakeDoc})
    sys.modules["docx.shared"] = type("S", (), {"Inches": lambda x: x})
    sys.modules["docx.oxml"] = type("O", (), {"OxmlElement": lambda name: type("E", (), {"set": lambda self, *a, **k: None, "text": ""})()})
    sys.modules["docx.oxml.ns"] = type("N", (), {"qn": lambda x: x})

    export_transcript(
        "hello",
        str(out),
        "docx",
        title="T",
        author="A",
        cover_image=str(cover),
        docx_cover_first=True,
        docx_footer_text="Footer",
        docx_footer_include_page_number=True,
    )
    assert out.exists() and out.read_bytes().startswith(b"DOCX")
