from types import SimpleNamespace

from podcast_transcriber import orchestrator as orch


def test_pick_quality_settings_variants():
    q = orch.pick_quality_settings("quick")
    assert q.get("whisper_model") == "base"
    q2 = orch.pick_quality_settings("premium")
    assert q2.get("whisper_model") == "large" and q2.get("topic_segmentation")
    q3 = orch.pick_quality_settings("standard")
    assert q3.get("whisper_model") == "small" and q3.get("chapter_minutes") == 10


def test_cmd_ingest_no_episodes(monkeypatch, tmp_path, capsys):
    cfg_file = tmp_path / "c.yml"
    cfg_file.write_text("{}", encoding="utf-8")

    class DummyYaml:
        @staticmethod
        def safe_load(s):
            return {}

    monkeypatch.setitem(__import__("sys").modules, "yaml", DummyYaml)
    monkeypatch.setattr(orch, "discover_new_episodes", lambda cfg, store: [])

    args = SimpleNamespace(config=str(cfg_file), feed=None)
    code = orch.cmd_ingest(args)
    assert code == 0
    assert "No new episodes" in capsys.readouterr().out

