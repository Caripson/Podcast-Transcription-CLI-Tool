# Orchestrator Configuration Guide

This page explains all supported keys for `podcast-cli run --config config.yml`, with copy‑paste examples. Use it with the Production Setup steps.

Related:
- Step‑by‑step deployment recipes: [Production Setup](production.md)
- Whisper language parameters: [Whisper Languages](whisper-languages.md)

📄 Minimal scaffold

```yaml
# config.yml
service: whisper                 # whisper | aws | gcp
quality: standard                # quick | standard | premium
language: null                   # auto-detect (or en, sv, es, ...)
output_dir: ./out                # where artifacts are saved

# Fallback Markdown when no outputs[] given
emit_markdown: true
# markdown_template: src/podcast_transcriber/templates/ebook.md.j2
feeds:
  - name: MyShow
    url: https://example.com/podcast/feed.xml
```

## Top-level keys

- service: whisper | aws | gcp
- quality: quick | standard | premium
- language: BCP‑47 or primary (e.g., `en`, `en-US`, `sv`)
- output_dir: path written for artifacts
- author: default author used in exports
- cover_image: path to an image to use as default cover
- keywords: list/CSV of keywords included in metadata
- emit_markdown: true to emit `.md` when `outputs:` is omitted
- markdown_template: path to a Jinja2 template for Markdown
- bilingual: true to try original + translated (Whisper only)
- clip_minutes: int to pre‑clip audio for faster runs
- nlp: enable semantic chapters and key takeaways

Example with common top‑level options

```yaml
service: whisper
quality: premium
language: en
output_dir: ./out
author: Jane Doe
cover_image: ./cover.jpg
keywords: [podcast, transcript, demo]
bilingual: false
clip_minutes: 2

nlp:
  semantic: true     # build topic chapters via embeddings
  takeaways: true    # add Key Takeaways section
```

## Quality presets (what they change)

- quick: small Whisper model (`base`), no diarization, no chaptering
- standard: Whisper `small`, summary enabled, chapter every ~10 minutes (when segments available)
- premium: Whisper `large`, summary enabled, semantic topic segmentation on, optional translation available

Note: Diarization only applies to AWS/GCP backends when set by the preset.

## Feeds

Define one or more podcast sources. You can use RSS URL, PodcastIndex ID, or Podcast GUID, plus optional category filtering.

Examples

```yaml
feeds:
  - name: MyFeed
    url: https://example.com/feed.xml

  - name: ById
    podcastindex_feedid: "12345"   # requires PODCASTINDEX_API_KEY/SECRET env vars

  - name: ByGuid
    podcast_guid: "podcast:abcd-efgh-..."
    categories: ["technology", "creative commons"]
```

## Outputs (multi‑format)

Define the formats you want under `outputs:`. If set, this suppresses `emit_markdown` fallback.

Common formats

```yaml
outputs:
  - { fmt: txt }
  - { fmt: md, md_include_cover: true }
  - { fmt: epub }
  - { fmt: pdf, pdf_font_file: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf }
  - { fmt: docx }
  - { fmt: srt }
  - { fmt: vtt }
  - { fmt: json }
```

Per‑format options supported

- pdf_font, pdf_font_size, pdf_margin
- pdf_cover_fullpage, pdf_first_page_cover_only
- pdf_page_size, pdf_orientation
- pdf_font_file: path to a Unicode font
- epub_css_file, epub_css_text
- auto_toc: true to build a table of contents (when supported)
- docx_cover_first, docx_cover_width_inches

Advanced example

```yaml
outputs:
  - fmt: pdf
    pdf_font_file: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
    pdf_cover_fullpage: true
    pdf_first_page_cover_only: true
    pdf_page_size: A4
    pdf_orientation: Portrait
  - fmt: epub
    epub_css_text: |
      h1 { font-family: serif; }
      p  { line-height: 1.5; }
  - fmt: md
    md_include_cover: true
```

## NLP block

Control semantic chaptering and key takeaways.

```yaml
nlp:
  semantic: true    # topic-based chapters
  takeaways: true   # bullet key takeaways
```

## Bilingual (Whisper)

Set `bilingual: true` to attempt two‑language output (Original + Translated) for Whisper. If translation fails, it falls back to original only.

```yaml
bilingual: true
service: whisper
```

## Markdown template

Point to a custom Jinja2 template to control Markdown output when `emit_markdown: true` or when you generate `md` in `outputs:`.

```yaml
emit_markdown: true
markdown_template: src/podcast_transcriber/templates/ebook.md.j2
```

## Quick run

```bash
podcast-cli run --config config.yml
```
