import io
from unittest import mock
import pytest

import podcast_transcriber.cli as cli


class DummyService:
    def __init__(self, text="TRANSCRIPT"):
        self.text = text

    def transcribe(self, audio_path: str, language=None) -> str:
        return self.text


def test_cli_credits_prints_and_exits(monkeypatch):
    buf = io.StringIO()
    with mock.patch("sys.stdout", buf):
        code = cli.main(["--credits"])
    assert code == 0
    assert "Podcast Transcription CLI Tool" in buf.getvalue()


def test_cli_theme_unknown_raises(tmp_path, monkeypatch):
    dummy_audio = tmp_path / "a.wav"
    dummy_audio.write_bytes(b"RIFF....")
    out_file = tmp_path / "out.epub"

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(dummy_audio),
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummyService()
    )

    with pytest.raises(SystemExit) as e:
        cli.main(
            [
                "--url",
                str(dummy_audio),
                "--service",
                "whisper",
                "--output",
                str(out_file),
                "--format",
                "epub",
                "--epub-theme",
                "does-not-exist",
            ]
        )
    assert e.value.code is not None


def test_cli_cache_hit_bypasses_transcribe(tmp_path, monkeypatch):
    dummy_audio = tmp_path / "b.wav"
    dummy_audio.write_bytes(b"RIFF....")

    # ensure local
    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(dummy_audio),
    )

    # Make cache.get return a hit payload and ensure transcribe is not used
    payload = {"text": "CACHED", "segments": None, "words": None}
    monkeypatch.setattr(
        "podcast_transcriber.utils.cache.get", lambda cache_dir, key: payload
    )

    class Svc:
        def transcribe(self, *a, **kw):  # pragma: no cover - should not be called
            raise AssertionError("transcribe should not be called when cache hit")

    monkeypatch.setattr("podcast_transcriber.services.get_service", lambda name: Svc())

    buf = io.StringIO()
    with mock.patch("sys.stdout", buf):
        code = cli.main(["--url", str(dummy_audio), "--service", "whisper"])
    assert code == 0
    assert buf.getvalue().strip().endswith("CACHED")


def test_cli_normalize_and_summarize_to_stdout(tmp_path, monkeypatch):
    dummy_audio = tmp_path / "c.wav"
    dummy_audio.write_bytes(b"RIFF....")

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(dummy_audio),
    )
    long_text = "Hello   world!  Extra spaces.\n\n\nNew para. Another sentence."
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummyService(long_text)
    )

    buf = io.StringIO()
    with mock.patch("sys.stdout", buf):
        code = cli.main(
            [
                "--url",
                str(dummy_audio),
                "--service",
                "whisper",
                "--normalize",
                "--summarize",
                "1",
            ]
        )
    assert code == 0
    out = buf.getvalue().strip()
    assert "  " not in out  # normalized spaces
    assert out and out[-1] in ".!?"  # summarized to 1 sentence
