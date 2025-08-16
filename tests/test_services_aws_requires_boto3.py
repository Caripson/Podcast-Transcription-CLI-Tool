import builtins

import pytest

from podcast_transcriber.services.aws_transcribe import AWSTranscribeService


def test_aws_transcribe_requires_boto3(monkeypatch, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "boto3":
            raise ImportError("no boto3")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    svc = AWSTranscribeService()
    with pytest.raises(RuntimeError):
        svc.transcribe(str(audio), language="en-US")
