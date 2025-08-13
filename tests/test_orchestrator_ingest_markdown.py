from pathlib import Path
from unittest import mock

def test_ingestion_by_feedid(monkeypatch):
    from podcast_transcriber.ingestion import feed as ing

    # Stub PodcastIndex by ID response
    def fake_by_id(feedid=None, guid=None):
        assert feedid == "123"
        return {
            "items": [
                {"id": "ep1", "title": "Episode 1", "link": "https://ex/1", "enclosureUrl": "https://ex/1.mp3"},
                {"id": "ep2", "title": "Episode 2", "link": "https://ex/2", "enclosureUrl": "https://ex/2.mp3"},
            ]
        }

    monkeypatch.setattr(ing, "_podcastindex_by_id", fake_by_id)

    class DummyStore:
        def __init__(self):
            self.seen = set()
        def has_seen(self, feed, key):
            return key in self.seen
        def mark_seen(self, feed, key):
            self.seen.add(key)

    cfg = {"feeds": [{"name": "feedid", "podcastindex_feedid": "123"}]}
    eps = ing.discover_new_episodes(cfg, DummyStore())
    assert len(eps) == 2
    assert eps[0]["source"].endswith(".mp3")


def test_ingestion_by_guid(monkeypatch):
    from podcast_transcriber.ingestion import feed as ing

    def fake_by_id(feedid=None, guid=None):
        assert guid == "guid-abc"
        return {
            "items": [
                {"id": "epx", "title": "Episode X", "link": "https://ex/x", "enclosureUrl": "https://ex/x.mp3"}
            ]
        }

    monkeypatch.setattr(ing, "_podcastindex_by_id", fake_by_id)
    cfg = {"feeds": [{"name": "feedguid", "podcast_guid": "guid-abc"}]}
    eps = ing.discover_new_episodes(cfg, type("S", (), {"has_seen": lambda *a, **k: False, "mark_seen": lambda *a, **k: None})())
    assert len(eps) == 1
    assert eps[0]["title"] == "Episode X"


def test_process_emits_markdown(tmp_path, monkeypatch):
    # Prepare fake ebooklib so EPUB write works without dependency
    class FakeBook:
        def set_title(self, t): pass
        def add_author(self, a): pass
        def set_cover(self, name, data): pass
        def add_item(self, item): pass
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
        def escape_html(self, s): return s
        def EpubNavi(self): return object()
        def EpubNav(self): return object()
        def EpubNCX(self): return object()
        def write_epub(self, path, book):
            Path(path).write_bytes(b"EPUB")

    import sys
    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    # Dummy transcription service
    class DummyService:
        def __init__(self):
            self.last_segments = None
        def transcribe(self, audio_path, language=None):
            return "Hello world"

    import podcast_transcriber.services as svc
    monkeypatch.setattr(svc, "get_service", lambda name: DummyService())

    # Isolate state directory
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))

    from podcast_transcriber.storage.state import StateStore
    store = StateStore()
    cfg = {
        "service": "whisper",
        "output_dir": str(tmp_path / "out"),
        "author": "Test",
        "emit_markdown": True,
    }
    job = store.create_job_with_episodes(cfg, [
        {"feed": "f", "title": "T", "slug": "t", "source": str(tmp_path / "audio.mp3")}
    ])
    # Prepare local fake audio
    (tmp_path / "audio.mp3").write_bytes(b"ID3....")

    from podcast_transcriber.orchestrator import cmd_process
    cmd_process(type("A", (), {"job_id": job["id"], "semantic": False})())

    out_epub = tmp_path / "out" / "t.epub"
    out_md = tmp_path / "out" / "t.md"
    assert out_epub.exists()
    assert out_md.exists() and "Hello world" in out_md.read_text(encoding="utf-8")


def test_markdown_includes_topics_and_takeaways(tmp_path, monkeypatch):
    # Fake ebooklib again
    class FakeBook:
        def set_title(self, t): pass
        def add_author(self, a): pass
        def set_cover(self, name, data): pass
        def add_item(self, item): pass
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
        def escape_html(self, s): return s
        def EpubNavi(self): return object()
        def EpubNav(self): return object()
        def EpubNCX(self): return object()
        def write_epub(self, path, book):
            Path(path).write_bytes(b"EPUB")

    import sys
    sys.modules["ebooklib"] = mock.MagicMock(epub=FakeEpubMod())
    sys.modules["ebooklib.epub"] = FakeEpubMod()

    # Service that returns a reasonably rich text for takeaways
    RICH_TEXT = (
        "Neural Networks and Machine Learning techniques for Podcast Analytics. "
        "Topic Segmentation improves Reader Experience and Content Discovery."
    )

    class RichService:
        def __init__(self):
            self.last_segments = None
        def transcribe(self, audio_path, language=None):
            return RICH_TEXT

    import podcast_transcriber.services as svc
    monkeypatch.setattr(svc, "get_service", lambda name: RichService())

    # Isolate state directory
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))

    from podcast_transcriber.storage.state import StateStore
    store = StateStore()
    cfg = {
        "service": "whisper",
        "output_dir": str(tmp_path / "out"),
        "author": "Test",
        "emit_markdown": True,
        "nlp": {"semantic": True, "takeaways": True},
    }
    job = store.create_job_with_episodes(cfg, [
        {"feed": "f", "title": "Episode Title", "slug": "episode", "source": str(tmp_path / "audio.mp3")}
    ])
    (tmp_path / "audio.mp3").write_bytes(b"ID3....")

    from podcast_transcriber.orchestrator import cmd_process
    cmd_process(type("A", (), {"job_id": job["id"], "semantic": True})())

    md = (tmp_path / "out" / "episode.md").read_text(encoding="utf-8")
    assert "## Topics" in md
    assert "## Key Takeaways" in md
    assert "-" in md  # at least one bullet under sections
