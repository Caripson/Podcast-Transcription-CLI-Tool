from abc import ABC, abstractmethod
from typing import Optional


class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """Return transcript text for a local audio file path."""
        raise NotImplementedError

