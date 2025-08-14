def test_discover_plugins_and_get(monkeypatch):
    import types
    import importlib

    from podcast_transcriber.services.base import TranscriptionService
    import podcast_transcriber.services as svc

    class DummyPlugin(TranscriptionService):
        def transcribe(self, audio_path: str, language=None) -> str:  # pragma: no cover
            return "x"

    class FakeEP:
        def __init__(self, name):
            self.name = name

        def load(self):
            return DummyPlugin

    # entry_points(group=...) should return list of FakeEP
    monkeypatch.setattr(
        importlib.metadata,  # type: ignore[attr-defined]
        "entry_points",
        lambda group=None: [FakeEP("X")],
        raising=False,
    )

    # Reset discovery cache
    svc._plugin_registry = None  # type: ignore[attr-defined]
    names = svc.list_service_names()
    assert "x" in [n.lower() for n in names]

    # get_service should instantiate plugin class
    inst = svc.get_service("x")
    assert isinstance(inst, TranscriptionService)

    # Unknown service should raise
    try:
        svc.get_service("unknown-service")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError for unknown service")
