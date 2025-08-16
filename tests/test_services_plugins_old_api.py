import importlib


def test_old_entry_points_api(monkeypatch):
    # Simulate Python 3.8/3.9 entry_points() returning a mapping
    class FakeEP:
        def __init__(self, name):
            self.name = name

        def load(self):
            class Dummy:
                def __call__(self):
                    return self

            return Dummy

    class OldAPI:
        def get(self, group, default=None):
            if group == "podcast_transcriber.services":
                return [FakeEP("dummy")]
            return []

    monkeypatch.setattr(
        importlib.metadata,  # type: ignore[attr-defined]
        "entry_points",
        lambda: OldAPI(),
        raising=False,
    )

    import podcast_transcriber.services as svc

    svc._plugin_registry = None  # type: ignore[attr-defined]
    names = svc.list_service_names()
    assert "dummy" in [n.lower() for n in names]

