# Example Fonts

This folder is intended for local fonts you can embed into PDFs via the `--pdf-font-file` flag.

Suggested free fonts (download and place `.ttf` here):
- Noto Serif Regular (Google Fonts): https://fonts.google.com/specimen/Noto+Serif
- Noto Sans Regular (Google Fonts): https://fonts.google.com/specimen/Noto+Sans

Usage example:

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format pdf \
  --pdf-font-file ./examples/fonts/NotoSerif-Regular.ttf \
  --output transcript.pdf
```

Note: Ensure the font license allows embedding. Google Fonts are typically licensed under the Open Font License (OFL).

