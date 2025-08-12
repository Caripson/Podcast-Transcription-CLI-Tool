import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Tuple


def _default_cache_dir() -> Path:
    base = os.environ.get("PODCAST_TRANSCRIBER_CACHE") or os.path.join(Path.home(), ".cache", "podcast_transcriber")
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def compute_key(
    source: str,
    service: str,
    opts: Tuple[str, ...],
    local_path: Optional[str] = None,
) -> str:
    h = hashlib.sha256()
    h.update(service.encode())
    h.update(b"\0")
    h.update(source.encode())
    if local_path and os.path.exists(local_path):
        st = os.stat(local_path)
        h.update(f"{st.st_size}:{int(st.st_mtime)}".encode())
    for o in opts:
        h.update(b"\0")
        h.update(o.encode())
    return h.hexdigest()


def get(cache_dir: Optional[str], key: str) -> Optional[dict]:
    dirp = Path(cache_dir) if cache_dir else _default_cache_dir()
    p = dirp / f"{key}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def set(cache_dir: Optional[str], key: str, payload: dict) -> None:
    dirp = Path(cache_dir) if cache_dir else _default_cache_dir()
    dirp.mkdir(parents=True, exist_ok=True)
    p = dirp / f"{key}.json"
    try:
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

