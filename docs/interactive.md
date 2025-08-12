# Interactive Mode

Use `--interactive` for a guided flow that prompts for the most common options. This is useful for first-time users or when you don’t want to remember flags.

How it works

- Prompts for: URL or local file, service, output format, output path (for non-txt), and optional language.
- Honors config defaults from `--config` or the discovered config file at `~/.config/podcast-transcriber/config.toml` (or `$XDG_CONFIG_HOME/podcast-transcriber/config.toml`).

Example session

```
$ podcast-transcriber --interactive
Vilken fil/URL vill du transkribera?: https://youtu.be/abc123
Tillgängliga tjänster:
  1. whisper
  2. aws
  3. gcp
Vilken tjänst vill du använda? (namn eller nummer): whisper
Tillgängliga format: azw, azw3, epub, json, kfx, md, mobi, pdf, srt, txt, vtt
Vilket output-format vill du ha? [txt]: json
Sökväg till outputfil? (krävs för icke-txt): out/transcript.json
Språkkod? (t.ex. sv, en-US) []:
```

Notes

- If you select `txt` and leave output empty, the transcript prints to stdout.
- All other formats require `--output` to be a file path.
- The service-specific options (e.g., AWS/GCP flags) can still be specified on the command line if needed.
