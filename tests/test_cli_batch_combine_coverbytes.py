from pathlib import Path

import podcast_transcriber.cli as cli


class DummyService:
    def transcribe(self, audio_path: str, language=None) -> str:
        return Path(audio_path).stem


def test_cli_batch_combine_cover_bytes_from_cover_url(tmp_path, monkeypatch):
    a1 = tmp_path / "a1.wav"
    a2 = tmp_path / "a2.wav"
    a1.write_bytes(b"RIFF..")
    a2.write_bytes(b"RIFF..")
    lst = tmp_path / "list.txt"
    lst.write_text(f"{a1}\n{a2}\n", encoding="utf-8")

    # ensure_local_audio returns LocalAudioPath with embedded cover bytes (no network)
    from podcast_transcriber.utils.downloader import LocalAudioPath

    def fake_ensure(s):
        lp = LocalAudioPath(str(s), is_temp=False)
        lp.cover_image_bytes = b"COV"
        return lp

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio", fake_ensure
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummyService()
    )

    # No network call needed when bytes are already present

    captured = {}

    def fake_export_book(chapters, out_path, fmt, **kwargs):
        captured["cover_image_bytes"] = kwargs.get("cover_image_bytes")
        Path(out_path).write_bytes(b"EPUB")

    monkeypatch.setattr("podcast_transcriber.exporters.export_book", fake_export_book)

    out_path = tmp_path / "book.epub"
    code = cli.main(
        [
            "--service",
            "whisper",
            "--input-file",
            str(lst),
            "--combine-into",
            str(out_path),
        ]
    )
    assert code == 0
    assert captured.get("cover_image_bytes") == b"COV"
