from pathlib import Path
from unittest import mock

from podcast_transcriber.exporters.exporter import export_book


def test_export_book_epub_with_metadata_and_cover(tmp_path, monkeypatch):
    out = tmp_path / "book.epub"

    chapters = [
        {"title": "Ch1", "text": "Hello"},
        {"title": "Ch2", "text": "World"},
    ]

    calls = {"set_lang": None, "desc": None, "subject": None, "cover": None}

    class FakeBook:
        def __init__(self):
            self.items = []
            self._lang = None

        def set_title(self, t):
            pass

        def add_author(self, a):
            pass

        def set_cover(self, name, data):
            preview = data[:4] if isinstance(data, (bytes, bytearray)) else data
            calls["cover"] = (name, preview)

        def add_item(self, item):
            self.items.append(item)

        def set_language(self, lang):
            calls["set_lang"] = lang

        def add_metadata(self, ns, key, value):
            if key == "description":
                calls["desc"] = value
            if key == "subject":
                calls["subject"] = value

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

        def EpubNav(self):
            return object()

        def EpubNavi(self):
            return object()

        def EpubNCX(self):
            return object()

        def EpubNcx(self):
            return object()

        def Link(self, *args, **kwargs):
            return object()

        def write_epub(self, path, book):
            Path(path).write_bytes(b"EPUB")

    import sys

    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    metadata = {
        "language": "en",
        "description": "Desk",
        "keywords": ["a", "b"],
    }

    export_book(
        chapters,
        str(out),
        "epub",
        title="T",
        author="A",
        cover_image=None,
        cover_image_bytes=b"JPEGDATA",
        metadata=metadata,
        epub_css_file=None,
        epub_css_text="p{font-size:12px}",
    )
    assert out.exists()
    # language, description, subject and cover were applied
    assert calls["set_lang"] == "en"
    assert calls["desc"] == "Desk"
    assert calls["subject"] == "a, b"
    assert calls["cover"] and calls["cover"][0] == "cover.jpg"
