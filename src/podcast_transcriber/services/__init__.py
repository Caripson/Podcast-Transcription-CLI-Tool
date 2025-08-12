from .base import TranscriptionService
from .whisper import WhisperService
from .aws_transcribe import AWSTranscribeService
from .gcp_speech import GCPSpeechService

_builtin_services = {
    "whisper": WhisperService,
    "aws": AWSTranscribeService,
    "gcp": GCPSpeechService,
}

_plugin_registry = None  # lazy-loaded


def _discover_plugins() -> dict:
    global _plugin_registry
    if _plugin_registry is not None:
        return _plugin_registry
    registry: dict[str, object] = {}
    try:
        # Python 3.10+: entry_points returns Selection
        from importlib.metadata import entry_points
        try:
            eps = entry_points(group="podcast_transcriber.services")
        except TypeError:
            # Python 3.8/3.9 fallback
            eps = entry_points().get("podcast_transcriber.services", [])  # type: ignore[attr-defined]
        for ep in eps:  # type: ignore[assignment]
            try:
                registry[ep.name.lower()] = ep.load()
            except Exception:
                # Ignore broken plugins; keep CLI functional
                continue
    except Exception:
        registry = {}
    _plugin_registry = registry
    return registry


def list_service_names() -> list[str]:
    names = set(_builtin_services.keys())
    names.update(_discover_plugins().keys())
    return sorted(names)


def get_service(name: str) -> TranscriptionService:
    name = (name or "").lower()
    if name in _builtin_services:
        cls = _builtin_services[name]
        return cls()  # type: ignore[call-arg]
    plugin = _discover_plugins().get(name)
    if plugin is None:
        raise ValueError(f"Unknown service: {name}")
    # Allow plugin to be a class or a factory returning an instance
    try:
        if isinstance(plugin, type) and issubclass(plugin, TranscriptionService):
            return plugin()  # type: ignore[call-arg]
    except Exception:
        pass
    inst = plugin()  # type: ignore[operator]
    if not isinstance(inst, TranscriptionService):
        raise TypeError(f"Plugin '{name}' did not return a TranscriptionService instance")
    return inst
