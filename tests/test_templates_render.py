from pathlib import Path
import sys
from types import SimpleNamespace

from podcast_transcriber.templates.render import render_markdown


def test_render_markdown(tmp_path, monkeypatch):
    # Provide a minimal fake jinja2 so the test doesn't require the extra
    def _select_autoescape():
        return None

    class _FileSystemLoader:
        def __init__(self, directory):
            self.directory = directory

    class _Template:
        def __init__(self, path):
            self.path = path

        def render(self, **ctx):
            txt = Path(self.path).read_text(encoding="utf-8")
            # Very simple replacement for this test
            for k, v in ctx.items():
                txt = txt.replace(f"{{{{ {k} }}}}", str(v))
            return txt

    class _Environment:
        def __init__(self, loader, autoescape=None):
            self.loader = loader

        def get_template(self, name):
            return _Template(Path(self.loader.directory) / name)

    fake_jinja2 = SimpleNamespace(
        Environment=_Environment,
        FileSystemLoader=_FileSystemLoader,
        select_autoescape=_select_autoescape,
    )
    monkeypatch.setitem(sys.modules, "jinja2", fake_jinja2)
    tpl = tmp_path / "t.md.j2"
    tpl.write_text("Hello {{ name }}", encoding="utf-8")
    out = render_markdown(str(tpl), {"name": "World"})
    assert out.strip() == "Hello World"
