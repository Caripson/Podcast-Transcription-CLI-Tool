import os
import re
import tempfile
from pathlib import Path
from typing import Union

import requests

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def is_url(s: str) -> bool:
    return bool(_URL_RE.match(s))


def ensure_local_audio(source: Union[str, os.PathLike]) -> str:
    """Ensure we have a local file path for the audio.

    - If `source` is a URL, this downloads to a temp file and returns its path.
    - If `source` is a local path, it returns the path after existence check.

    The returned string may have attribute `_is_temp` set to True on the string object,
    which we use for cleanup in the CLI.
    """
    s = str(source)
    if is_url(s):
        resp = requests.get(s, stream=True, timeout=60)
        resp.raise_for_status()
        suffix = _guess_extension_from_headers(resp.headers) or ".audio"
        fd, tmp_path = tempfile.mkstemp(prefix="podcast_", suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
        except Exception:
            # Clean up partially written file
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise
        # Mark as temp via attribute on the string (hacky but effective here)
        try:
            setattr(tmp_path, "_is_temp", True)  # type: ignore[attr-defined]
        except Exception:
            pass
        return tmp_path

    # local path
    p = Path(s)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {s}")
    return str(p)


def _guess_extension_from_headers(headers) -> str:
    ct = headers.get("content-type", "").lower()
    if "mpeg" in ct or "mp3" in ct:
        return ".mp3"
    if "wav" in ct:
        return ".wav"
    if "x-m4a" in ct or "m4a" in ct:
        return ".m4a"
    if "aac" in ct:
        return ".aac"
    if "ogg" in ct:
        return ".ogg"
    return ""

