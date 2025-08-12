from .base import TranscriptionService
from .whisper import WhisperService
from .aws_transcribe import AWSTranscribeService
from .gcp_speech import GCPSpeechService


def get_service(name: str) -> TranscriptionService:
    name = name.lower()
    if name == "whisper":
        return WhisperService()
    if name == "aws":
        return AWSTranscribeService()
    if name == "gcp":
        return GCPSpeechService()
    raise ValueError(f"Unknown service: {name}")

