import sys

import pytest


def make_fake_whisper(record):
    class FakeModel:
        def transcribe(self, audio_path, language=None, task=None):
            record["calls"].append(
                {
                    "audio_path": audio_path,
                    "language": language,
                    "task": task,
                }
            )
            # Minimal structure resembling Whisper output
            return {"text": "ok", "segments": []}

    class FakeWhisperModule:
        def load_model(self, name):
            record["model_name"] = name
            return FakeModel()

    return FakeWhisperModule()


def test_whisper_language_normalization_en_us(monkeypatch, tmp_path):
    # Prepare dummy audio file
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")

    # Record calls
    record = {"calls": []}

    # Inject fake whisper module and bypass dependency checks
    sys.modules["whisper"] = make_fake_whisper(record)
    # Provide minimal tokenizer mapping so service can validate codes
    sys.modules["whisper.tokenizer"] = type(
        "_Tok", (), {"TO_LANGUAGE_CODE": {"english": "en", "javanese": "jw"}}
    )()
    import podcast_transcriber.services.whisper as ws

    monkeypatch.setattr(ws.WhisperService, "_check_dependencies", lambda self: None)

    svc = ws.WhisperService()
    out = svc.transcribe(str(audio), language="en-US")

    assert out == "ok"
    assert record["calls"], "model.transcribe was not called"
    # Should normalize en-US -> en
    assert record["calls"][0]["language"] == "en"


def test_whisper_language_unsupported_falls_back_autodetect(monkeypatch, tmp_path):
    audio = tmp_path / "b.wav"
    audio.write_bytes(b"RIFF....")

    record = {"calls": []}
    sys.modules["whisper"] = make_fake_whisper(record)
    sys.modules["whisper.tokenizer"] = type(
        "_Tok", (), {"TO_LANGUAGE_CODE": {"english": "en", "javanese": "jw"}}
    )()
    import podcast_transcriber.services.whisper as ws

    monkeypatch.setattr(ws.WhisperService, "_check_dependencies", lambda self: None)

    svc = ws.WhisperService()
    out = svc.transcribe(str(audio), language="xx-YY")

    assert out == "ok"
    # Fallback to autodetect (None) for unsupported code
    assert record["calls"][0]["language"] is None
