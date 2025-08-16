import builtins

import pytest

from podcast_transcriber.services.aws_transcribe import AWSTranscribeService


def test_aws_transcribe_requires_bucket(monkeypatch, tmp_path):
    # Provide a dummy boto3 so import succeeds
    class DummyBoto3:
        @staticmethod
        def client(name, region_name=None):
            class C:
                def upload_file(self, *a, **k):
                    pass

            return C()

    monkeypatch.setitem(__import__("sys").modules, "boto3", DummyBoto3())
    # Ensure bucket env is missing
    monkeypatch.delenv("AWS_TRANSCRIBE_S3_BUCKET", raising=False)
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")
    svc = AWSTranscribeService()
    with pytest.raises(RuntimeError):
        svc.transcribe(str(audio), language="en-US")

