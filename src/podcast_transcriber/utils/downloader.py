import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Union
from urllib.parse import urlparse


# 'requests' is a core dependency but import it lazily so the CLI can start
def _require_requests():
    try:
        import requests  # type: ignore

        return requests
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Python package 'requests' is required for downloading URLs.\n"
            "Install project dependencies, e.g.:\n"
            "  python -m venv .venv && source .venv/bin/activate && pip install -e .\n"
            "Or: pip install requests"
        ) from e


_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def is_url(s: str) -> bool:
    return bool(_URL_RE.match(s))


class LocalAudioPath(str):
    """String subclass carrying whether the path is temporary.

    Behaves like ``str`` so existing code/tests that expect a path string keep working,
    while exposing ``.is_temp`` for reliable cleanup.
    """

    def __new__(cls, value: str, is_temp: bool = False):
        obj = super().__new__(cls, value)
        obj.is_temp = is_temp  # type: ignore[attr-defined]
        # Back-compat for older attribute name
        try:
            obj._is_temp = is_temp
        except Exception:
            pass
        return obj


def _http_get(url: str, **kwargs):
    retries = int(kwargs.pop("retries", 3))
    backoff = float(kwargs.pop("backoff", 1.5))
    last_exc = None
    for i in range(retries):
        try:
            return _require_requests().get(url, **kwargs)
        except Exception as e:
            last_exc = e
            if i == retries - 1:
                break
            import time

            time.sleep(backoff ** (i + 1))
    if last_exc:
        raise last_exc
    raise RuntimeError("HTTP GET failed without exception")


def ensure_local_audio(source: Union[str, os.PathLike]) -> str:
    """Ensure we have a local file path for the audio.

    - If `source` is a URL, this downloads to a temp file and returns its path.
    - If `source` is a local path, it returns the path after existence check.

    Returns a ``str`` (actually a ``LocalAudioPath``) that has ``.is_temp`` set to True
    when a temporary file was created.
    """
    s = str(source)
    if is_url(s):
        # Special handling: YouTube via yt-dlp if available
        try:
            u = urlparse(s)
            host = (u.netloc or "").lower()
        except Exception:
            host = ""
        if "youtube.com" in host or "youtu.be" in host:
            if shutil.which("yt-dlp"):
                fd, tmp_path = tempfile.mkstemp(prefix="podcast_", suffix=".m4a")
                os.close(fd)
                try:
                    info_title = None
                    info_thumb = None
                    try:
                        out = subprocess.check_output(["yt-dlp", "-J", s])
                        import json

                        data = json.loads(out.decode("utf-8", errors="ignore"))
                        info_title = data.get("title")
                        info_thumb = data.get("thumbnail")
                        info_uploader = data.get("uploader")
                    except Exception:
                        pass
                    subprocess.run(
                        ["yt-dlp", "-x", "--audio-format", "m4a", "-o", tmp_path, s],
                        check=True,
                    )
                    lp = LocalAudioPath(tmp_path, is_temp=True)
                    if info_title:
                        lp.source_title = info_title
                    if info_thumb:
                        lp.cover_url = info_thumb
                    try:
                        if info_uploader:
                            lp.source_uploader = info_uploader
                    except Exception:
                        pass
                    return lp
                except Exception:
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass
                    # fall through to generic HTTP
                    pass
        # RSS/Podcast feed: attempt to resolve first enclosure
        if s.endswith(".xml") or "rss" in s.lower() or "feed" in s.lower():
            try:
                import xml.etree.ElementTree as ET

                r = _require_requests().get(s, timeout=30)
                r.raise_for_status()
                root = ET.fromstring(r.text)
                # Try common namespaces
                enclosure_url = None
                for item in root.iter("item"):
                    enc = item.find("enclosure")
                    if enc is not None and enc.get("url"):
                        enclosure_url = enc.get("url")
                        break
                if enclosure_url:
                    return ensure_local_audio(enclosure_url)
            except Exception:
                pass

        resp = _http_get(s, stream=True, timeout=60)
        resp.raise_for_status()
        suffix = _guess_extension_from_headers(resp.headers) or ".audio"
        fd, tmp_path = tempfile.mkstemp(prefix="podcast_", suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as fh:
                total = int(resp.headers.get("content-length", 0))
                sofar = 0
                verbose = os.environ.get("PODCAST_TRANSCRIBER_VERBOSE") == "1"
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
                        if verbose and total:
                            sofar += len(chunk)
                            pct = int(sofar * 100 / total)
                            print(
                                f"Downloading... {pct}%",
                                end="\r",
                                file=__import__("sys").stderr,
                            )
        except Exception:
            # Clean up partially written file
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise
        # Return a string subclass that carries temp flag
        lp = LocalAudioPath(tmp_path, is_temp=True)
        _try_enrich_id3(lp)
        return lp

    # local path
    p = Path(s)
    if not p.exists():
        raise FileNotFoundError(f"Audio file not found: {s}")
    lp = LocalAudioPath(str(p), is_temp=False)
    _try_enrich_id3(lp)
    return lp


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


def _try_enrich_id3(lp: LocalAudioPath) -> None:
    try:
        from mutagen.id3 import ID3  # type: ignore
    except Exception:
        return
    try:
        tags = ID3(str(lp))
        title = tags.get("TIT2")
        artist = tags.get("TPE1")
        if title and getattr(title, "text", None):
            lp.id3_title = str(title.text[0])
        if artist and getattr(artist, "text", None):
            lp.id3_artist = str(artist.text[0])
        for k in (k for k in tags.keys() if k.startswith("APIC")):
            apic = tags.get(k)
            if apic and getattr(apic, "data", None):
                lp.cover_image_bytes = bytes(apic.data)
                break
    except Exception:
        return
