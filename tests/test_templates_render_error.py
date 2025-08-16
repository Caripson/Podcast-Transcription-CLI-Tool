import builtins

import pytest


def test_render_markdown_requires_jinja2(monkeypatch, tmp_path):
    # Remove jinja2 to trigger RuntimeError in render_markdown
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "jinja2":
            raise ImportError("no jinja2")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    from podcast_transcriber.templates.render import render_markdown

    tpl = tmp_path / "t.md.j2"
    tpl.write_text("Hello", encoding="utf-8")
    with pytest.raises(RuntimeError):
        render_markdown(str(tpl), {})

