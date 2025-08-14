import io
from unittest import mock

import podcast_transcriber.cli as cli


class DummyService:
    def __init__(self, text="TRANSCRIPT"):
        self.text = text
        self.calls = []

    def transcribe(self, audio_path: str, language=None) -> str:
        self.calls.append((audio_path, language))
        return self.text


def test_cli_writes_to_stdout(tmp_path, monkeypatch):
    dummy_audio = tmp_path / "a.wav"
    dummy_audio.write_bytes(b"RIFF....")

    # Ensure local audio bypasses network
    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(dummy_audio),
    )
    service = DummyService("hello world")
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service",
        lambda name: service,
    )

    stdout = io.StringIO()
    with mock.patch("sys.stdout", stdout):
        code = cli.main(["--url", str(dummy_audio), "--service", "whisper"])

    assert code == 0
    assert stdout.getvalue().strip() == "hello world"
    assert service.calls and service.calls[0][0].endswith("a.wav")


def test_cli_writes_to_file(tmp_path, monkeypatch):
    dummy_audio = tmp_path / "b.mp3"
    dummy_audio.write_bytes(b"ID3....")
    out_file = tmp_path / "out.txt"

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(dummy_audio),
    )
    service = DummyService("Hej transcript")
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service",
        lambda name: service,
    )

    code = cli.main(
        [
            "--url",
            str(dummy_audio),
            "--service",
            "whisper",
            "--output",
            str(out_file),
        ]
    )
    assert code == 0
    assert out_file.read_text(encoding="utf-8").strip() == "Hej transcript"
