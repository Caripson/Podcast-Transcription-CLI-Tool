import json
from pathlib import Path

import podcast_transcriber.cli as cli


class SvcWithSegments:
    def __init__(self, text="TEXT", segments=None):
        self.text = text
        # expose last_segments like whisper/aws would
        self.last_segments = segments or [
            {"start": 0.0, "end": 1.0, "text": "Hello"},
            {"start": 2.0, "end": 3.5, "text": "World"},
        ]

    def transcribe(self, audio_path: str, language=None) -> str:
        return self.text


def test_cli_kdp_sets_epub_and_auto_toc(tmp_path, monkeypatch):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")
    out = tmp_path / "book.epub"

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(audio),
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service",
        lambda name: SvcWithSegments("Hello World"),
    )

    captured = {}

    def fake_export_transcript(text, out_path, fmt, **kwargs):
        captured["fmt"] = fmt
        captured["auto_toc"] = kwargs.get("auto_toc", False)
        Path(out_path).write_bytes(b"EPUB")

    monkeypatch.setattr(
        "podcast_transcriber.exporters.export_transcript", fake_export_transcript
    )

    code = cli.main(
        [
            "--url",
            str(audio),
            "--service",
            "whisper",
            "--output",
            str(out),
            "--kdp",
        ]
    )
    assert code == 0
    assert out.exists()
    # KDP defaults to EPUB and auto_toc enabled
    assert captured.get("fmt") == "epub"
    assert captured.get("auto_toc") is True


def test_cli_json_metadata_includes_source_and_fields(tmp_path, monkeypatch):
    audio = tmp_path / "b.wav"
    audio.write_bytes(b"RIFF....")
    out = tmp_path / "t.json"

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(audio),
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service",
        lambda name: SvcWithSegments("Hello World"),
    )

    code = cli.main(
        [
            "--url",
            str(audio),
            "--service",
            "whisper",
            "--output",
            str(out),
            "--format",
            "json",
            "--language",
            "en-US",
            "--description",
            "Desc",
            "--keywords",
            "foo, bar",
            "--subtitle",
            "Sub",
            "--series-title",
            "S",
            "--volume-number",
            "1",
        ]
    )
    assert code == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    # Ensure source metadata present
    src = data.get("source")
    assert isinstance(src, dict)
    assert src.get("source_url") == str(audio)
    assert Path(src.get("local_path")).name == audio.name
    # KDP metadata fields propagated
    assert src.get("language") == "en-US"
    assert src.get("description") == "Desc"
    assert src.get("keywords") == ["foo", "bar"]
    assert src.get("subtitle") == "Sub"
    assert src.get("series_title") == "S"
    assert src.get("volume_number") == "1"
