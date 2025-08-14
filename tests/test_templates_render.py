import importlib
import pytest


def test_render_markdown_requires_jinja(monkeypatch, tmp_path):
    # Ensure importing jinja2 fails to exercise the RuntimeError branch
    # (we only assert the error message, not the import machinery).
    monkeypatch.setitem(importlib.sys.modules, "jinja2", None)
    from podcast_transcriber.templates.render import render_markdown

    tpl = tmp_path / "t.md.j2"
    tpl.write_text("Hello", encoding="utf-8")
    with pytest.raises(RuntimeError):
        render_markdown(str(tpl), {"x": 1})
