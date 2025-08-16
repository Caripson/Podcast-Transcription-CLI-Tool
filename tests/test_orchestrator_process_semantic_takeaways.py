from types import SimpleNamespace

from podcast_transcriber import orchestrator as orch


class DummyService:
    def __init__(self, text):
        self.text = text
        self.last_segments = [
            {"start": 0.0, "end": 60.0, "text": "Hello"},
            {"start": 60.0, "end": 120.0, "text": "World"},
        ]

    def transcribe(self, audio_path: str, language=None) -> str:
        return self.text


def test_process_episode_semantic_and_takeaways(monkeypatch):
    # Avoid downloading
    monkeypatch.setattr(orch, "ensure_local_audio", lambda s: s)
    # Provide dummy service via registry
    monkeypatch.setattr(orch.services, "get_service", lambda name: DummyService("A B C"))
    # Semantic topics
    monkeypatch.setattr(
        orch, "segment_with_embeddings", lambda text: [{"title": "T1", "text": text}]
    )
    # Takeaways
    monkeypatch.setattr(orch, "key_takeaways_better", lambda text: ["k1", "k2"])

    ep = {"source": "/tmp/a.wav", "title": "Title", "description": "Desc"}
    res = orch._process_episode(
        ep,
        service_name="whisper",
        quality="standard",
        language="en-US",
        nlp_cfg={"semantic": True, "takeaways": True},
        clip_minutes=None,
    )
    assert res["chapters"] and res["takeaways"] == ["k1", "k2"]

