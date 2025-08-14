import importlib


class SegService:
    def __init__(self, segs):
        self.last_segments = segs

    def transcribe(self, audio_path, language=None):
        return "text"


def test_orchestrator_chapter_minutes(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))
    orch = importlib.import_module("podcast_transcriber.orchestrator")

    # Make sure we use a tiny chapter_minutes via pick_quality_settings
    monkeypatch.setattr(orch, "pick_quality_settings", lambda q: {"chapter_minutes": 1, "summarize": False})
    # Provide segments totaling > 60s to force a split
    segs = [
        {"start": 0.0, "end": 40.0, "text": "A"},
        {"start": 40.0, "end": 85.0, "text": "B"},  # 45s
        {"start": 85.0, "end": 100.0, "text": "C"},
    ]
    monkeypatch.setattr("podcast_transcriber.services.get_service", lambda name: SegService(segs))
    monkeypatch.setattr("podcast_transcriber.orchestrator.ensure_local_audio", lambda s: str(tmp_path / "a.wav"))
    res = orch._process_episode({"source": str(tmp_path / "a.wav"), "title": "T"}, "whisper", "standard", None, nlp_cfg={})
    assert isinstance(res["chapters"], list) and len(res["chapters"]) >= 2


def test_orchestrator_takeaways(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))
    orch = importlib.import_module("podcast_transcriber.orchestrator")
    # No segmentation, but ask for takeaways
    monkeypatch.setattr("podcast_transcriber.services.get_service", lambda name: SegService(None))
    monkeypatch.setattr("podcast_transcriber.orchestrator.ensure_local_audio", lambda s: str(tmp_path / "a.wav"))
    monkeypatch.setattr(orch, "key_takeaways_better", lambda text: ["K1", "K2"])  # force takeaways
    res = orch._process_episode({"source": str(tmp_path / "a.wav"), "title": "T"}, "whisper", "standard", None, nlp_cfg={"takeaways": True})
    assert res.get("takeaways") == ["K1", "K2"]

