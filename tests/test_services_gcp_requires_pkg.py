import builtins

import pytest

from podcast_transcriber.services.gcp_speech import GCPSpeechService



def test_gcp_speech_requires_google_cloud(monkeypatch, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name.startswith("google.cloud"):
            raise ImportError("no google cloud speech")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    svc = GCPSpeechService()
    with pytest.raises(RuntimeError):
        svc.transcribe(str(audio), language="en-US")
