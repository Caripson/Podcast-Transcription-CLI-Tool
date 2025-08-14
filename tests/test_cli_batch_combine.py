from pathlib import Path
from unittest import mock

import podcast_transcriber.cli as cli


class DummyService:
    def __init__(self, text):
        self.text = text

    def transcribe(self, audio_path: str, language=None) -> str:
        return self.text


def test_cli_batch_combine_into_epub(tmp_path, monkeypatch):
    # Create two local audio placeholders
    a1 = tmp_path / "a1.wav"; a1.write_bytes(b"RIFF..")
    a2 = tmp_path / "a2.wav"; a2.write_bytes(b"RIFF..")
    lst = tmp_path / "list.txt"; lst.write_text(f"{a1}\n{a2}\n", encoding="utf-8")

    # Ensure local path passthrough
    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(Path(s)),
    )

    # Service returns different texts per file to emulate chapters
    texts = {str(a1): "Hello A1", str(a2): "Hello A2"}

    class Svc(DummyService):
        def transcribe(self, audio_path: str, language=None) -> str:
            return texts[audio_path]

    monkeypatch.setattr("podcast_transcriber.services.get_service", lambda name: Svc(""))

    # Patch export_book to just write a file and capture payload
    calls = {}

    def fake_export_book(chapters, out_path, fmt, **kwargs):
        Path(out_path).write_bytes(b"EPUB")
        calls["chapters"] = chapters
        calls["fmt"] = fmt

    monkeypatch.setattr("podcast_transcriber.exporters.export_book", fake_export_book)

    out_path = tmp_path / "book.epub"
    code = cli.main([
        "--service", "whisper",
        "--url", str(a1),
        "--input-file", str(lst),
        "--combine-into", str(out_path),
        "--format", "epub",
    ])
    assert code == 0
    assert out_path.exists()
    assert calls.get("fmt") == "epub"
    # Expect two chapters
    chs = calls.get("chapters", [])
    assert isinstance(chs, list) and len(chs) == 2
    assert any("Hello A1" in c.get("text", "") for c in chs)
    assert any("Hello A2" in c.get("text", "") for c in chs)
