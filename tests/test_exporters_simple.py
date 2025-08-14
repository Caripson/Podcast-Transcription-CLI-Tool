import json

from podcast_transcriber.exporters.exporter import export_transcript


def test_export_srt_basic(tmp_path):
    out = tmp_path / "t.srt"
    segs = [
        {"start": 0.0, "end": 1.5, "text": "Hello"},
        {"start": 2.0, "end": 3.0, "text": "World", "speaker": "S1"},
    ]
    export_transcript("Hello\n\nWorld", str(out), "srt", segments=segs)
    data = out.read_text(encoding="utf-8")
    assert "00:00:00,000" in data and "00:00:01,500" in data
    assert "S1: World" in data


def test_export_json_with_words_and_meta(tmp_path):
    out = tmp_path / "t.json"
    segs = [{"start": 0.0, "end": 1.0, "text": "Hi"}]
    words = [
        {"start": 0.0, "end": 0.3, "word": "Hi"},
    ]
    meta = {"source_url": "u", "local_path": "/p"}
    export_transcript(
        "Hi",
        str(out),
        "json",
        segments=segs,
        words=words,
        title="T",
        author="A",
        metadata=meta,
    )
    obj = json.loads(out.read_text(encoding="utf-8"))
    assert obj["title"] == "T" and obj["author"] == "A"
    assert isinstance(obj.get("segments"), list) and obj.get("words")[0]["word"] == "Hi"
    assert obj.get("source")["local_path"] == "/p"
