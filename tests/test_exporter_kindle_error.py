import pytest

from podcast_transcriber.exporters import exporter as exp


def test_export_kindle_requires_calibre(monkeypatch, tmp_path):
    out = tmp_path / "book.azw3"
    # Ensure which returns None to simulate missing ebook-convert
    monkeypatch.setattr(exp.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError):
        exp._export_kindle(
            text="hello",
            out_path=str(out),
            target_fmt="azw3",
            title="T",
            author="A",
            cover_image=None,
            css_file=None,
            css_text=None,
        )

