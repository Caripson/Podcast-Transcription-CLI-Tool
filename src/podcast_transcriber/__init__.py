try:
    from importlib.metadata import version as _pkg_version  # Python 3.8+
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore

def _resolve_version() -> str:
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
