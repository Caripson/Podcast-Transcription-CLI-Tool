import builtins

import pytest

from podcast_transcriber import orchestrator as orch


def test_load_yaml_config_requires_pyyaml(monkeypatch, tmp_path):
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "yaml":
            raise ImportError("no pyyaml")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(SystemExit):
        orch.load_yaml_config(str(tmp_path / "c.yml"))


def test_load_yaml_config_missing_file(monkeypatch, tmp_path):
    # yaml present but file missing
    class DummyYaml:
        @staticmethod
        def safe_load(s):
            return {}

    monkeypatch.setitem(__import__("sys").modules, "yaml", DummyYaml)
    with pytest.raises(SystemExit):
        orch.load_yaml_config(str(tmp_path / "missing.yml"))

