from unittest import mock

import pytest

from podcast_transcriber.services.aws_transcribe import AWSTranscribeService


def test_aws_transcribe_failure_path(monkeypatch, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")

    # Mock env bucket/region
    monkeypatch.setenv("AWS_TRANSCRIBE_S3_BUCKET", "my-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    s3_client = mock.Mock()

    class FakeTranscribe:
        def __init__(self):
            self.calls = 0

        def start_transcription_job(self, **kw):
            return None

        def get_transcription_job(self, TranscriptionJobName):
            # Immediately return FAILED state
            return {
                "TranscriptionJob": {
                    "TranscriptionJobStatus": "FAILED",
                    "FailureReason": "Boom",
                }
            }

    transcribe_client = FakeTranscribe()

    def fake_client(name, region_name=None):
        if name == "s3":
            return s3_client
        if name == "transcribe":
            return transcribe_client
        raise AssertionError("unexpected client")

    # Patch boto3
    monkeypatch.setitem(__import__("sys").modules, "boto3", mock.Mock(client=fake_client))

    svc = AWSTranscribeService()
    with pytest.raises(RuntimeError):
        svc.transcribe(str(audio), language="en-US")
    # Should attempt to delete the temp object on failure
    assert s3_client.delete_object.called

