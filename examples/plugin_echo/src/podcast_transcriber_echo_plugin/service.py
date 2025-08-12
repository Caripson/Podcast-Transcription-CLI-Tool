from typing import Optional

from podcast_transcriber.services.base import TranscriptionService


class EchoService(TranscriptionService):
    name = "echo"

    def __init__(self) -> None:
        self.last_segments = []
        self.last_words = []

    def transcribe(self, local_path: str, language: Optional[str] = None) -> str:
        # Minimal demonstration service: echo the path and synthesize a tiny segment
        self.last_segments = [{"start": 0.0, "end": 0.0, "text": f"ECHO: {local_path}"}]
        self.last_words = []
        return f"ECHO: {local_path}"

