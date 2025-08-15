import sys
from pathlib import Path


def test_orchestrator_multi_outputs(tmp_path, monkeypatch):
    # Fake ebooklib so EPUB export works without dependency
    class FakeBook:
        def set_title(self, t):
            pass

        def add_author(self, a):
            pass

        def set_cover(self, name, data):
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

        def EpubNav(self):
            return object()

        def EpubNcx(self):
            return object()

        def write_epub(self, path, book):
            Path(path).write_bytes(b"EPUB")

    sys.modules["ebooklib"] = __import__("types").SimpleNamespace(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    # Dummy transcription service
    class DummyService:
        def __init__(self):
            self.last_segments = [
                {"start": 0.0, "end": 1.0, "text": "Hello"},
                {"start": 1.0, "end": 2.0, "text": "World"},
            ]

        def transcribe(self, audio_path, language=None):
            return "Hello\n\nWorld"

    import podcast_transcriber.services as svc

    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))
    monkeypatch.setattr(svc, "get_service", lambda name: DummyService())

    from podcast_transcriber.storage.state import StateStore

    store = StateStore()
    out_dir = tmp_path / "out"
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"JPG")

    cfg = {
        "service": "whisper",
        "output_dir": str(out_dir),
        "author": "Test",
        "cover_image": str(cover),
        "outputs": [
            {"fmt": "epub"},
            {"fmt": "md", "md_include_cover": True},
            {
                "fmt": "pdf",
                "pdf_font": "Arial",
                "pdf_font_size": 12,
                "pdf_margin": 15,
            },
            {"fmt": "docx", "docx_cover_first": True, "docx_cover_width_inches": 6.0},
            {"fmt": "json"},
            {"fmt": "srt"},
            {"fmt": "vtt"},
            {"fmt": "txt"},
        ],
    }
    # Prepare audio
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"ID3....")
    job = store.create_job_with_episodes(
        cfg,
        [
            {
                "feed": "f",
                "title": "Episode",
                "slug": "episode",
                "source": str(audio),
            }
        ],
    )

    from podcast_transcriber.orchestrator import cmd_process

    rc = cmd_process(type("A", (), {"job_id": job["id"], "semantic": False})())
    assert rc == 0
    # Verify a subset of outputs created
    assert (out_dir / "episode.epub").exists()
    assert (out_dir / "episode.pdf").exists()
    assert (out_dir / "episode.docx").exists()
    assert (out_dir / "episode.md").exists()
    assert (out_dir / "episode.json").exists()

