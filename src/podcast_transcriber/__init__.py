from typing import Optional

try:
    from importlib.metadata import version as _pkg_version  # Python 3.8+
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore


def _read_pyproject_version() -> Optional[str]:
    try:
        # Prefer the version declared in the local pyproject.toml when running from source
        from pathlib import Path
        this_file = Path(__file__).resolve()
        for parent in this_file.parents:
            p = parent / "pyproject.toml"
            if p.exists():
                text = p.read_text(encoding="utf-8")
                # Try tomllib/tomli parsing first
                try:
                    try:
                        import tomllib  # py311+
                    except Exception:  # pragma: no cover
                        import tomli as tomllib  # type: ignore
                    data = tomllib.loads(text)
                    proj = data.get("project") or {}
                    ver = proj.get("version")
                    if isinstance(ver, str) and ver.strip():
                        return ver.strip()
                except Exception:
                    # Fallback to a simple regex if toml lib is unavailable
                    import re
                    m = re.search(r"^version\s*=\s*\"([^\"]+)\"", text, re.MULTILINE)
                    if m:
                        return m.group(1).strip()
                break
    except Exception:
        return None
    return None


def _resolve_version() -> str:
    # Prefer the version from pyproject when present (source tree)
    ver = _read_pyproject_version()
    if isinstance(ver, str) and ver:
        return ver
    # Otherwise fall back to installed package metadata
    if _pkg_version is not None:
        try:
            return _pkg_version("podcast-transcriber")
        except Exception:
            pass
    return "dev"

__version__ = _resolve_version()
__credits__ = "Developed by Johan Caripson"
__version_display__ = f"{__version__} — {__credits__}"

__all__ = [
    "cli",
    "services",
    "__version__",
    "__credits__",
    "__version_display__",
]
