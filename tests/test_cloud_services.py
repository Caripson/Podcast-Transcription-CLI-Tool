import json
from unittest import mock

from podcast_transcriber.services.aws_transcribe import AWSTranscribeService
from podcast_transcriber.services.gcp_speech import GCPSpeechService


def test_aws_transcribe_minimal_flow(monkeypatch, tmp_path):
    # Arrange: create dummy audio file
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")

    # Mock env
    monkeypatch.setenv("AWS_TRANSCRIBE_S3_BUCKET", "my-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    # Mock boto3 S3 and Transcribe clients
    s3_client = mock.Mock()
    transcribe_client = mock.Mock()

    def fake_client(name, region_name=None):
        if name == "s3":
            return s3_client
        if name == "transcribe":
            return transcribe_client
        raise AssertionError("unexpected client")

    monkeypatch.setitem(__import__("sys").modules, "boto3", mock.Mock(client=fake_client))

    # Prepare get_transcription_job to return COMPLETED with TranscriptFileUri
    transcribe_client.get_transcription_job.return_value = {
        "TranscriptionJob": {
            "TranscriptionJobStatus": "COMPLETED",
            "Transcript": {
                "TranscriptFileUri": "https://example.com/t.json",
            },
        }
    }

    # Mock requests.get for transcript JSON
    transcript_payload = {
        "results": {"transcripts": [{"transcript": "hello"}, {"transcript": "world"}]}
    }
    fake_resp = mock.Mock()
    fake_resp.json.return_value = transcript_payload
    fake_resp.raise_for_status.return_value = None
    monkeypatch.setattr("requests.get", lambda url, timeout=60: fake_resp)

    svc = AWSTranscribeService()
    text = svc.transcribe(str(audio), language="en-US")
    assert text == "hello world"


def test_gcp_speech_minimal_flow(monkeypatch, tmp_path):
    # Arrange a tiny audio file
    audio = tmp_path / "b.wav"
    audio.write_bytes(b"RIFF....")

    # Build fake google.cloud.speech module
    class FakeAlt:
        def __init__(self, transcript):
            self.transcript = transcript

    class FakeResult:
        def __init__(self, txt):
            self.alternatives = [FakeAlt(txt)]

    class FakeResponse:
        def __init__(self, txt):
            self.results = [FakeResult(txt)]

    class FakeConfig:
        class AudioEncoding:
            ENCODING_UNSPECIFIED = 0

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeAudio:
        def __init__(self, content):
            self.content = content

    class FakeClient:
        def recognize(self, config, audio):
            return FakeResponse("Hej världen")

    fake_speech = mock.MagicMock()
    fake_speech.SpeechClient = FakeClient
    fake_speech.RecognitionAudio = FakeAudio
    fake_speech.RecognitionConfig = FakeConfig

    fake_google_cloud = mock.MagicMock()
    fake_google_cloud.speech = fake_speech

    # Insert into sys.modules chain
    import sys

    sys.modules["google"] = mock.MagicMock()
    sys.modules["google.cloud"] = fake_google_cloud
    sys.modules["google.cloud.speech"] = fake_speech

    svc = GCPSpeechService()
    text = svc.transcribe(str(audio), language="sv-SE")
    assert "Hej" in text

