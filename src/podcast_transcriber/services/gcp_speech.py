from typing import Optional

from .base import TranscriptionService


class GCPSpeechService(TranscriptionService):
    """Minimal Google Cloud Speech-to-Text integration.

    Requirements:
    - google-cloud-speech installed
    - GCP credentials configured (e.g., GOOGLE_APPLICATION_CREDENTIALS)
    """

    def __init__(self, alternative_language_codes: Optional[list[str]] = None) -> None:
        self._alt_langs = alternative_language_codes or []

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        try:
            from google.cloud import speech  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "GCP Speech-to-Text requires 'google-cloud-speech'. Install with: pip install google-cloud-speech"
            ) from e

        client = speech.SpeechClient()
        with open(audio_path, "rb") as f:
            content = f.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            language_code=language or "en-US",
            encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
            enable_automatic_punctuation=True,
            alternative_language_codes=self._alt_langs or None,
        )
        response = client.recognize(config=config, audio=audio)
        # Concatenate all results
        parts = []
        for result in getattr(response, "results", []) or []:
            alt = getattr(result, "alternatives", [])
            if alt:
                parts.append(getattr(alt[0], "transcript", ""))
        return " ".join(p.strip() for p in parts if p).strip()
