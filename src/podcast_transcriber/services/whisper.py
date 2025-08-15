import shutil
from typing import Dict, List, Optional

from .base import TranscriptionService


class WhisperService(TranscriptionService):
    def __init__(
        self,
        model: str = "base",
        translate: bool = False,
        chunk_seconds: Optional[int] = None,
    ) -> None:
        self.model_name = model
        self.translate = translate
        self.chunk_seconds = chunk_seconds
        self.last_segments: List[Dict] = []
        self.last_words: List[Dict] = []

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

        # Normalize language codes to what Whisper expects (e.g., en-US -> en).
        # If unsupported after normalization, let Whisper auto-detect by using None.
        norm_lang: Optional[str] = None
        if language:
            try:
                from whisper.tokenizer import TO_LANGUAGE_CODE  # type: ignore

                valid_codes = set(TO_LANGUAGE_CODE.values())
            except Exception:
                valid_codes = set()
            lang = (language or "").strip().lower().replace("_", "-")
            if lang in ("auto", "detect", "auto-detect"):
                norm_lang = None
            else:
                # Reduce BCP-47 like en-us, pt-br to primary subtag
                primary = lang.split("-", 1)[0]
                # Some common aliases/corrections could go here if needed
                # e.g., map jv->jw (Javanese) per Whisper's codes
                if primary == "jv":
                    primary = "jw"
                # Use only if Whisper recognizes it; otherwise None for autodetect
                norm_lang = primary if (not valid_codes or primary in valid_codes) else None
        else:
            norm_lang = None

        if self.chunk_seconds:
            # Chunk with ffmpeg into temp dir and merge results with offsets
            import os
            import subprocess
            import tempfile
            from pathlib import Path

            tempdir = tempfile.mkdtemp(prefix="wchunks_")
            pat = os.path.join(tempdir, "chunk_%05d.wav")
            # segment into fixed-length chunks
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    audio_path,
                    "-f",
                    "segment",
                    "-segment_time",
                    str(int(self.chunk_seconds)),
                    "-c",
                    "copy",
                    pat,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            text_parts = []
            base_offset = 0.0
            all_segments: List[Dict] = []
            all_words: List[Dict] = []
            for chunk in sorted(Path(tempdir).glob("chunk_*.wav")):
                result = model.transcribe(
                    str(chunk),
                    language=norm_lang,
                    task=("translate" if self.translate else None),
                )
                t = (result.get("text") or "").strip()
                if t:
                    text_parts.append(t)
                for seg in result.get("segments", []) or []:
                    all_segments.append(
                        {
                            "start": float(seg.get("start", 0.0)) + base_offset,
                            "end": float(seg.get("end", 0.0)) + base_offset,
                            "text": str(seg.get("text", "")).strip(),
                        }
                    )
                    # word-level if present
                    for w in seg.get("words", []) or []:
                        all_words.append(
                            {
                                "start": float(w.get("start", 0.0)) + base_offset,
                                "end": float(w.get("end", 0.0)) + base_offset,
                                "word": str(w.get("word", "")),
                            }
                        )
                base_offset += float(self.chunk_seconds)
            # cleanup chunks
            try:
                for f in Path(tempdir).glob("*"):
                    try:
                        f.unlink()
                    except Exception:
                        pass
                Path(tempdir).rmdir()
            except Exception:
                pass
            self.last_segments = all_segments
            self.last_words = all_words
            return "\n\n".join(text_parts).strip()
        else:
            result = model.transcribe(
                audio_path,
                language=norm_lang,
                task=("translate" if self.translate else None),
            )
            text = (result.get("text") or "").strip()
            # capture segments and words if present
            segs = []
            words = []
            for seg in result.get("segments", []) or []:
                segs.append(
                    {
                        "start": float(seg.get("start", 0.0)),
                        "end": float(seg.get("end", 0.0)),
                        "text": str(seg.get("text", "")).strip(),
                    }
                )
                for w in seg.get("words", []) or []:
                    words.append(
                        {
                            "start": float(w.get("start", 0.0)),
                            "end": float(w.get("end", 0.0)),
                            "word": str(w.get("word", "")),
                        }
                    )
            self.last_segments = segs
            self.last_words = words
            return text
