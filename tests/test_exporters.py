from pathlib import Path
from unittest import mock

from podcast_transcriber.exporters.exporter import export_transcript, infer_format_from_path


def test_infer_format_from_path_variants():
    assert infer_format_from_path("a.txt") == "txt"
    assert infer_format_from_path("b.PDF") == "pdf"
    assert infer_format_from_path("c.doc") is None
    assert infer_format_from_path(None) is None


def test_txt_export(tmp_path):
    out = tmp_path / "t.txt"
    export_transcript("hello", str(out), "txt")
    assert out.read_text(encoding="utf-8").strip() == "hello"


def test_pdf_export_with_fake_fpdf(tmp_path, monkeypatch):
    out = tmp_path / "t.pdf"
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"JPEGDATA")

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

        def multi_cell(self, *args, **kwargs):
            pass

        def ln(self, *args, **kwargs):
            pass

        def output(self, path):
            Path(path).write_bytes(b"%PDF-1.4\n...")

        def image(self, *args, **kwargs):
            # accept any image call
            pass

    fake_fpdf_mod = mock.MagicMock(FPDF=FakePDF)
    import sys

    sys.modules["fpdf"] = fake_fpdf_mod
    export_transcript(
        "hello",
        str(out),
        "pdf",
        title="T",
        author="A",
        pdf_font="Arial",
        pdf_font_size=10,
        pdf_margin=20,
        cover_image=str(cover),
        pdf_cover_fullpage=True,
    )

def test_pdf_cover_only_page_then_text(tmp_path, monkeypatch):
    out = tmp_path / "t2.pdf"
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"JPEGDATA")

    class FakePDF2:
        def __init__(self, *args, **kwargs):
            self.pages = 0
            self.l_margin = 10
            self.w = 210

        def set_auto_page_break(self, auto=True, margin=15):
            pass

        def add_page(self):
            self.pages += 1

        def set_title(self, t):
            pass

        def set_author(self, a):
            pass

        def set_font(self, *args, **kwargs):
            pass

        def multi_cell(self, *args, **kwargs):
            pass

        def ln(self, *args, **kwargs):
            pass

        def image(self, *args, **kwargs):
            pass

        def output(self, path):
            Path(path).write_bytes(b"%PDF-1.4\n...")

    fake_fpdf_mod = mock.MagicMock(FPDF=FakePDF2)
    import sys

    sys.modules["fpdf"] = fake_fpdf_mod
    export_transcript(
        "hello",
        str(out),
        "pdf",
        title="T",
        author="A",
        pdf_font="Arial",
        pdf_font_size=10,
        pdf_margin=20,
        cover_image=str(cover),
        pdf_first_page_cover_only=True,
    )
    assert out.exists()
    assert out.exists() and out.stat().st_size > 0


def test_epub_to_kindle_calls_ebook_convert(tmp_path, monkeypatch):
    out = tmp_path / "t.azw3"

    # Pretend ebook-convert exists
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/ebook-convert" if name == "ebook-convert" else None)

    # Fake ebooklib.epub
    class FakeBook:
        def set_title(self, t):
            pass

        def add_author(self, a):
            pass

        def add_item(self, item):
            pass

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

        def escape_html(self, s):
            return s

        def EpubNavi(self):
            return object()

        def EpubNav(self):
            return object()

        def EpubNCX(self):
            return object()

        def Link(self, *args, **kwargs):
            return object()

        def write_epub(self, path, book):
            Path(path).write_bytes(b"EPUB")

    import sys

    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    ran = {}

    def fake_run(cmd, check=True):
        ran["cmd"] = cmd
        # Simulate output creation
        Path(cmd[-1]).write_bytes(b"KINDLE")

    monkeypatch.setattr("subprocess.run", fake_run)

    export_transcript("hello world", str(out), "azw3", title="T")
    assert out.exists() and out.read_bytes().startswith(b"KINDLE")
    assert ran["cmd"][0].endswith("ebook-convert")


def test_epub_with_cover_calls_set_cover(tmp_path, monkeypatch):
    out = tmp_path / "t.epub"
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"JPEG")

    called = {"set_cover": False}

    class FakeBook:
        def set_title(self, t):
            pass

        def add_author(self, a):
            pass

        def set_cover(self, name, data):
            called["set_cover"] = True

        def add_item(self, item):
            pass

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

        def escape_html(self, s):
            return s

        def EpubNavi(self):
            return object()

        def EpubNav(self):
            return object()

        def EpubNCX(self):
            return object()

        def Link(self, *args, **kwargs):
            return object()

        def write_epub(self, path, book):
            Path(path).write_bytes(b"EPUB")

    import sys

    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    export_transcript("hello", str(out), "epub", title="T", cover_image=str(cover))
    assert out.exists()
    assert called["set_cover"]


def test_epub_embeds_css(tmp_path, monkeypatch):
    out = tmp_path / "t.epub"
    css = tmp_path / "style.css"
    css.write_text("p{color:red}", encoding="utf-8")

    captured = {"html": None}

    class FakeBook:
        def __init__(self):
            self.items = []

        def set_title(self, t):
            pass

        def add_author(self, a):
            pass

        def set_cover(self, name, data):
            pass

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

        def escape_html(self, s):
            return s

        def EpubNavi(self):
            return object()

        def EpubNav(self):
            return object()

        def EpubNCX(self):
            return object()

        def Link(self, *args, **kwargs):
            return object()

        def write_epub(self, path, book):
            # capture html
            for it in book.items:
                if isinstance(it, FakeHtml):
                    captured["html"] = it.content
            Path(path).write_bytes(b"EPUB")

    import sys

    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    export_transcript("hello", str(out), "epub", title="T", epub_css_file=str(css))
    assert out.exists()
    assert "<style>p{color:red}</style>" in captured["html"]


def test_cover_resize_with_pillow(tmp_path, monkeypatch):
    out = tmp_path / "t.epub"
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"PNG")

    class FakeImg:
        def __init__(self):
            self.size = (4000, 4000)

        def convert(self, mode):
            return self

        def thumbnail(self, size, resample):
            self.size = size

        def save(self, buf, format="JPEG", quality=85):
            buf.write(b"JPEGDATA")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakePILImage:
        LANCZOS = 1

        @staticmethod
        def open(path):
            return FakeImg()

    import sys

    sys.modules["PIL"] = mock.MagicMock()
    sys.modules["PIL.Image"] = FakePILImage

    # Fake ebooklib again
    class FakeBook2:
        def set_title(self, t):
            pass

        def add_author(self, a):
            pass

        def set_cover(self, name, data):
            # ensure our resized bytes were used
            assert data.startswith(b"JPEGDATA")

        def add_item(self, item):
            pass

    class FakeHtml2:
        def __init__(self, title, file_name, lang):
            self.title = title
            self.file_name = file_name
            self.lang = lang
            self.content = ""

    class FakeEpubMod2:
        def __init__(self):
            self.EpubBook = FakeBook2
            self.EpubHtml = FakeHtml2

        def escape_html(self, s):
            return s

        def EpubNavi(self):
            return object()

        def EpubNav(self):
            return object()

        def EpubNCX(self):
            return object()

        def Link(self, *args, **kwargs):
            return object()

        def write_epub(self, path, book):
            Path(path).write_bytes(b"EPUB")

    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod2())
    sys.modules["ebooklib.epub"] = FakeEpubMod2()

    export_transcript("hello", str(out), "epub", title="T", cover_image=str(cover))
    assert out.exists()
