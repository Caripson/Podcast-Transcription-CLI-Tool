import shutil
from typing import Optional

from .base import TranscriptionService


class WhisperService(TranscriptionService):
    def __init__(self, model: str = "base") -> None:
        self.model_name = model

    def _check_dependencies(self) -> None:
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "ffmpeg is required for Whisper. Please install ffmpeg first."
            )
        try:
            import whisper  # noqa: F401
        except Exception as e:
            raise RuntimeError(
                "Python package 'openai-whisper' is required for local Whisper.\n"
                "Install with: pip install openai-whisper"
            ) from e

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        # Lazy import to avoid hard dependency for users not using whisper
        self._check_dependencies()
        import whisper  # type: ignore

        model = whisper.load_model(self.model_name)
        result = model.transcribe(audio_path, language=language)
        text = result.get("text") or ""
        return text.strip()

