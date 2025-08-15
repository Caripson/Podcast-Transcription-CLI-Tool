import json
from pathlib import Path

from podcast_transcriber.exporters.exporter import export_transcript


def test_json_includes_words_and_metadata(tmp_path):
    out = tmp_path / "t.json"
    segs = [
        {"start": 0.0, "end": 1.0, "text": "Hello"},
    ]
    words = [
        {"start": 0.0, "end": 0.2, "word": "He"},
        {"start": 0.2, "end": 0.5, "word": "llo"},
    ]
    meta = {"source_url": "x", "local_path": "/tmp/a.wav", "language": "en"}
    export_transcript(
        "Hello",
        str(out),
        "json",
        title="MyTitle",
        author="Auth",
        segments=segs,
        words=words,
        metadata=meta,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["title"] == "MyTitle" and data["author"] == "Auth"
    assert data["segments"][0]["text"].startswith("Hello")
    assert data.get("words") and data["source"]["language"] == "en"
