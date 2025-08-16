import importlib

import pytest

import podcast_transcriber.services as svc



def test_plugin_factory_returns_wrong_type(monkeypatch):
    class BadFactory:
        def __call__(self):
            return object()

    class FakeEP:
        def __init__(self, name):
            self.name = name

        def load(self):
            return BadFactory

    # Patch entry_points to return our bad plugin
    monkeypatch.setattr(
        importlib.metadata,  # type: ignore[attr-defined]
        "entry_points",
        lambda group=None: [FakeEP("bad")],
        raising=False,
    )

    svc._plugin_registry = None  # type: ignore[attr-defined]
    names = svc.list_service_names()
    assert "bad" in [n.lower() for n in names]
    with pytest.raises(TypeError):
        svc.get_service("bad")
