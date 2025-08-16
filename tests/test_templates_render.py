from pathlib import Path

from podcast_transcriber.templates.render import render_markdown


def test_render_markdown(tmp_path, monkeypatch):
    tpl = tmp_path / "t.md.j2"
    tpl.write_text("Hello {{ name }}", encoding="utf-8")
    out = render_markdown(str(tpl), {"name": "World"})
    assert out.strip() == "Hello World"
