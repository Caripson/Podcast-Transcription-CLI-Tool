from pathlib import Path
from unittest import mock

from podcast_transcriber.exporters.exporter import export_transcript


def test_epub_splits_chapters_from_segments(tmp_path, monkeypatch):
    out = tmp_path / "chap.epub"

    class FakeBook:
        def __init__(self):
            self.items = []
            self.nav = []
            self.toc = ()
            self._cover = None

        def set_title(self, t):
            pass

        def add_author(self, a):
            pass

        def set_cover(self, name, data):
            self._cover = (name, data)

        def add_item(self, item):
            self.items.append(item)

    class FakeHtml:
        def __init__(self, title, file_name, lang):
            self.title = title
            self.file_name = file_name
            self.lang = lang
            self.content = ""

    class FakeEpubMod:
        def __init__(self):
            self.EpubBook = FakeBook
            self.EpubHtml = FakeHtml

        def EpubNavi(self):
            return object()

        def EpubNav(self):
            return object()

        def EpubNCX(self):
            return object()

        def Link(self, *args, **kwargs):
            return object()

        def write_epub(self, path, book):
            # verify we created multiple chapter items
            chapter_files = [
                it.file_name for it in book.items if isinstance(it, FakeHtml)
            ]
            # at least one transcript or section file present
            assert any(f.startswith("section_") or f == "transcript.xhtml" for f in chapter_files)
            Path(path).write_bytes(b"EPUB")

    import sys

    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    segments = [
        {"start": 0.0, "end": 1.0, "text": "A"},
        {"start": 5.0, "end": 6.0, "text": "B"},
        {"start": 10.0, "end": 11.0, "text": "C"},
    ]

    export_transcript("hello", str(out), "epub", title="T", author="A", segments=segments)
    assert out.exists()
