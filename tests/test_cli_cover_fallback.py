from pathlib import Path

import podcast_transcriber.cli as cli
from podcast_transcriber.utils.downloader import LocalAudioPath


class DummySvc:
    def transcribe(self, *a, **k):
        return "TXT"


def test_cli_cover_fallback_requests_used(tmp_path, monkeypatch):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF..")
    out = tmp_path / "t.epub"

    # Return LocalAudioPath with cover_url set
    def fake_ensure(src):
        lp = LocalAudioPath(str(audio), is_temp=False)
        lp.cover_url = "https://example.com/cover.jpg"
        return lp

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio", fake_ensure
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummySvc()
    )

    # Fake requests.get used by CLI to fetch cover bytes
    class Resp:
        def __init__(self):
            self.content = b"COVERBYTES"

        def raise_for_status(self):
            return None

    monkeypatch.setattr("requests.get", lambda *a, **k: Resp(), raising=False)

    captured = {}

    def fake_export(text, out_path, fmt, **kwargs):
        captured["cover_image_bytes"] = kwargs.get("cover_image_bytes")
        Path(out_path).write_bytes(b"EPUB")

    monkeypatch.setattr("podcast_transcriber.exporters.export_transcript", fake_export)

    code = cli.main(
        [
            "--url",
            str(audio),
            "--service",
            "whisper",
            "--output",
            str(out),
            "--format",
            "epub",
        ]
    )
    assert code == 0
    assert captured.get("cover_image_bytes") == b"COVERBYTES"
