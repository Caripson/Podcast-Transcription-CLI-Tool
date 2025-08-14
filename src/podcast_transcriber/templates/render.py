from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def render_markdown(template_path: str, context: Dict[str, Any]) -> str:
    try:
        from jinja2 import (  # type: ignore
            Environment,
            FileSystemLoader,
            select_autoescape,
        )
    except Exception as e:
        raise RuntimeError(
            "Jinja2 is required for templated rendering. Install with: pip install jinja2 or podcast-transcriber[templates]"
        ) from e
    p = Path(template_path)
    env = Environment(
        loader=FileSystemLoader(str(p.parent)), autoescape=select_autoescape()
    )
    tmpl = env.get_template(p.name)
    return tmpl.render(**context)
