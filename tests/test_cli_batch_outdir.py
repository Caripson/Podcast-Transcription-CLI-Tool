from pathlib import Path

import podcast_transcriber.cli as cli


class DummyService:
    def __init__(self, text="BATCH"):
        self.text = text

    def transcribe(self, audio_path: str, language=None) -> str:
        return f"{self.text}:{Path(audio_path).stem}"


def test_cli_batch_outputs_to_directory(tmp_path, monkeypatch):
    # Create two local audio placeholders
    a1 = tmp_path / "a1.wav"
    a1.write_bytes(b"RIFF..")
    a2 = tmp_path / "a2.wav"
    a2.write_bytes(b"RIFF..")
    lst = tmp_path / "list.txt"
    lst.write_text(f"{a1}\n{a2}\n", encoding="utf-8")

    # Ensure local path passthrough
    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(Path(s)),
    )
    # Use dummy service
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummyService()
    )

    out_dir = tmp_path / "out"
    code = cli.main(
        [
            "--service",
            "whisper",
            "--input-file",
            str(lst),
            "--output",
            str(out_dir),
            "--format",
            "txt",
        ]
    )
    assert code == 0
    # Expect per-item outputs in directory
    assert (out_dir / "a1.txt").exists()
    assert (out_dir / "a2.txt").exists()
