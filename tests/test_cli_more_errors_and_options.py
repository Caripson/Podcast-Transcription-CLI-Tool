from pathlib import Path
import pytest

import podcast_transcriber.cli as cli


class DummyService:
    def __init__(self, text="TXT"):
        self.text = text
        self.last_segments = None
        self.last_words = None

    def transcribe(self, audio_path: str, language=None) -> str:
        return self.text


def test_cli_non_txt_requires_output(tmp_path, monkeypatch):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF..")
    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(audio),
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummyService()
    )
    with pytest.raises(SystemExit) as e:
        cli.main(["--url", str(audio), "--service", "whisper", "--format", "pdf"])
    assert "--output is required" in str(e.value)


def test_cli_epub_theme_custom_css(tmp_path, monkeypatch):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF..")
    css = tmp_path / "style.css"
    css.write_text("p{font:12px sans-serif}", encoding="utf-8")
    out = tmp_path / "t.epub"

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(audio),
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummyService()
    )

    captured = {}

    def fake_export_transcript(text, out_path, fmt, **kwargs):
        captured.update(kwargs)
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
            "--format",
            "epub",
            "--epub-theme",
            f"custom:{css}",
        ]
    )
    assert code == 0
    assert captured.get("epub_css_text") and "p{font:" in captured["epub_css_text"]


def test_cli_json_auto_title_and_source_title(tmp_path, monkeypatch):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF..")
    out = tmp_path / "t.json"

    from podcast_transcriber.utils.downloader import LocalAudioPath

    def fake_ensure(s):
        lp = LocalAudioPath(str(audio), is_temp=False)
        lp.source_title = "My Source Title"
        return lp

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio", fake_ensure
    )
    monkeypatch.setattr(
        "podcast_transcriber.services.get_service", lambda name: DummyService("text")
    )

    captured = {}

    def fake_export(text, out_path, fmt, **kwargs):
        captured["metadata"] = kwargs.get("metadata")
        Path(out_path).write_bytes(b"JSON")

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
            "json",
        ]
    )
    assert code == 0
    md = captured["metadata"]
    assert md["source_title"] == "My Source Title"
