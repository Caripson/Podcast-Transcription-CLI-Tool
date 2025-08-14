from typing import Dict, List, Optional

from .base import TranscriptionService


class GCPSpeechService(TranscriptionService):
    """Minimal Google Cloud Speech-to-Text integration.

    Requirements:
    - google-cloud-speech installed
    - GCP credentials configured (e.g., GOOGLE_APPLICATION_CREDENTIALS)
    """

    def __init__(
        self,
        alternative_language_codes: Optional[list[str]] = None,
        speakers: Optional[int] = None,
        long_running: bool = False,
    ) -> None:
        self._alt_langs = alternative_language_codes or []
        self._speakers = speakers
        self._long_running = long_running
        self.last_segments: List[Dict] = []
        self.last_words: List[Dict] = []

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
        diarization_config = None
        if self._speakers and self._speakers > 0:
            diarization_config = speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=1,
                max_speaker_count=int(self._speakers),
            )
        config = speech.RecognitionConfig(
            language_code=language or "en-US",
            encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
            enable_automatic_punctuation=True,
            alternative_language_codes=self._alt_langs or None,
            diarization_config=diarization_config,
        )
        if self._long_running:
            operation = client.long_running_recognize(config=config, audio=audio)
            response = operation.result()
        else:
            response = client.recognize(config=config, audio=audio)
        # Gather transcript and word-level timings if present
        parts = []
        words: List[Dict] = []
        for result in getattr(response, "results", []) or []:
            alt = getattr(result, "alternatives", [])
            if alt:
                a0 = alt[0]
                parts.append(getattr(a0, "transcript", ""))
                for w in getattr(a0, "words", []) or []:
                    st = getattr(
                        getattr(w, "start_time", None), "total_seconds", lambda: 0.0
                    )()
                    et = getattr(
                        getattr(w, "end_time", None), "total_seconds", lambda: 0.0
                    )()
                    words.append(
                        {
                            "start": float(st),
                            "end": float(et),
                            "word": getattr(w, "word", ""),
                            "speaker": getattr(w, "speaker_tag", None),
                        }
                    )
        # Build speaker segments if any speaker info present
        segments: List[Dict] = []
        cur: List[Dict] = []
        cur_spk = None
        for w in words:
            spk = w.get("speaker")
            if spk != cur_spk and cur:
                segments.append(
                    {
                        "start": cur[0]["start"],
                        "end": cur[-1]["end"],
                        "text": " ".join(x.get("word", "") for x in cur).strip(),
                        "speaker": cur_spk,
                    }
                )
                cur = []
            cur.append(w)
            cur_spk = spk
        if cur:
            segments.append(
                {
                    "start": cur[0]["start"],
                    "end": cur[-1]["end"],
                    "text": " ".join(x.get("word", "") for x in cur).strip(),
                    "speaker": cur_spk,
                }
            )
        self.last_words = words
        self.last_segments = segments
        return " ".join(p.strip() for p in parts if p).strip()
