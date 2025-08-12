# 📚 Examples: Output Formats

Below are sample commands to export transcripts to various formats.

## TXT

```bash
./Transcribe_podcast_to_text.sh \
  --url "https://example.com/podcast.mp3" \
  --service whisper \
  --output transcript.txt
```

## PDF (with basic styling)

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format pdf \
  --title "My Show" \
  --author "Host" \
  --pdf-font Arial \
  --pdf-font-size 12 \
  --pdf-margin 20 \
  --pdf-orientation landscape \
  --output transcript.pdf
```

## EPUB (with cover)

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
--format epub \
--title "My Show" \
--author "Host" \
--cover-image ./path/to/cover.jpg \
--output transcript.epub
```

EPUB with custom CSS:

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format epub \
  --title "My Show" \
  --author "Host" \
  --epub-css-file ./path/to/style.css \
  --output transcript.epub
```

## Kindle (AZW3)

Requires Calibre's `ebook-convert` in PATH.

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format azw3 \
  --title "My Show" \
  --author "Host" \
  --cover-image ./path/to/cover.jpg \
  --output transcript.azw3
```

Other Kindle formats supported: `mobi`, `azw`, `kfx`.

## PDF (embedded font for Unicode)

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format pdf \
  --pdf-font-file ./examples/fonts/NotoSerif-Regular.ttf \
  --output transcript.pdf
```
