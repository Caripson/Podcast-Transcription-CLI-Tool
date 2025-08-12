from .base import TranscriptionService

# Optional backends are imported lazily to avoid hard dependencies at import time
# so the CLI can start even if extras (requests/boto3/gcloud) are not installed.
try:
    from .whisper import WhisperService  # type: ignore
except Exception:
    WhisperService = None  # type: ignore[assignment]

try:
    from .aws_transcribe import AWSTranscribeService  # type: ignore
except Exception:
    AWSTranscribeService = None  # type: ignore[assignment]

try:
    from .gcp_speech import GCPSpeechService  # type: ignore
except Exception:
    GCPSpeechService = None  # type: ignore[assignment]

_builtin_services = {}
if WhisperService is not None:
    _builtin_services["whisper"] = WhisperService  # type: ignore[index]
if AWSTranscribeService is not None:
    _builtin_services["aws"] = AWSTranscribeService  # type: ignore[index]
if GCPSpeechService is not None:
    _builtin_services["gcp"] = GCPSpeechService  # type: ignore[index]

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
    names = set(["whisper", "aws", "gcp"])  # advertise built-in names always
    names.update(_discover_plugins().keys())
    return sorted(names)


def get_service(name: str) -> TranscriptionService:
    name = (name or "").lower()
    if name in ("whisper", "aws", "gcp"):
        # Import lazily to surface clear errors only when selected
        try:
            if name == "whisper":
                from .whisper import WhisperService as _WS  # type: ignore
                return _WS()  # type: ignore[call-arg]
            if name == "aws":
                from .aws_transcribe import AWSTranscribeService as _AWS  # type: ignore
                return _AWS()  # type: ignore[call-arg]
            if name == "gcp":
                from .gcp_speech import GCPSpeechService as _GCP  # type: ignore
                return _GCP()  # type: ignore[call-arg]
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                f"Failed to initialize service '{name}'. Install required dependencies for this backend."
            ) from e
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
