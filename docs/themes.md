# 🎨 Built-in Themes and PDF Covers

This tool provides several built-in EPUB themes and flexible PDF cover handling.

## EPUB Themes

- `minimal`: Clean sans-serif, compact spacing, great for general reading.
- `reader`: Serif font with larger size and line-height for long-form reading.

Enable via:

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format epub \
  --epub-theme reader \
  --output transcript.epub
```

Preview (example screenshots):

![Minimal theme](img/theme-minimal.png)
![Reader theme](img/theme-reader.png)

Also available: `classic`.

## Markdown Templates (Jinja2)

The Markdown exporter supports Jinja2 templates so you can control structure and styling of the generated `.md` documents.

- Base template: `src/podcast_transcriber/templates/ebook.md.j2`
- Extend it and override blocks like `front_matter`, `title_page`, `preface`, `content`, `appendix`.

Example custom template:

```jinja2
{% extends 'ebook.md.j2' %}

{% block title_page %}
# {{ title }}
_by {{ author }}_

{% if cover_image %}
![Cover]({{ cover_image }})
{% endif %}
{% endblock %}

{% block content %}
{% if summary %}
## Summary
{{ summary }}
{% endif %}

{% for ch in chapters %}
## {{ ch.title }}
{{ ch.text }}
{% endfor %}
{% endblock %}
```

How to use:

- CLI: `--format md --output out.md` only for simple built-in layout.
- Orchestrator:
  - Global: `emit_markdown: true` + `markdown_template: ./path/to/template.md.j2`.
  - Per output: `outputs: [ { fmt: md, template: ./template.md.j2 } ]`.

## PDF Cover Options

- `--cover-image`: Adds a cover image before the transcript.
- `--pdf-cover-fullpage`: Renders the cover as a dedicated full-page; transcript begins on the next page.

Example:

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format pdf \
  --cover-image ./cover.jpg \
  --pdf-cover-fullpage \
  --output transcript.pdf
```

Preview (example screenshot):

![PDF cover fullpage](img/pdf-cover-fullpage.png)

Notes

- If Pillow is installed, cover images are auto-resized to a Kindle-friendly max resolution.
- You can also provide your own CSS via `--epub-css-file` which is combined with any built-in theme.
