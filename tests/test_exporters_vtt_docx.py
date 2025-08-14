from pathlib import Path

from podcast_transcriber.exporters.exporter import export_transcript


def test_export_vtt_basic(tmp_path):
    out = tmp_path / "t.vtt"
    segs = [
        {"start": 0.0, "end": 1.0, "text": "A"},
        {"start": 1.0, "end": 2.5, "text": "B", "speaker": "S"},
    ]
    export_transcript("A\n\nB", str(out), "vtt", segments=segs)
    data = out.read_text(encoding="utf-8")
    assert data.startswith("WEBVTT")
    assert "00:00:01.000" in data and "S: B" in data


def test_export_docx_with_fake_module(tmp_path, monkeypatch):
    out = tmp_path / "t.docx"

    class FakeDoc:
        def __init__(self):
            self.lines = []

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

    fake_docx = type("M", (), {"Document": FakeDoc})
    import sys

    sys.modules["docx"] = fake_docx
    # Provide minimal shared.Inches to satisfy import path
    sys.modules["docx.shared"] = type("S", (), {"Inches": lambda x: x})
    # Minimal attribute for successful save
    export_transcript("Hello", str(out), "docx", title="T", author="A")
    assert out.exists() and out.read_bytes().startswith(b"DOCX")
