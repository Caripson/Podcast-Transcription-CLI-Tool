import argparse
import sys
from pathlib import Path

from .utils.downloader import ensure_local_audio
from . import services


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="podcast-transcriber",
        description="Transcribe a podcast audio from a URL or file using pluggable services.",
    )
    p.add_argument("--url", required=True, help="Audio URL or local file path")
    p.add_argument(
        "--service",
        required=True,
        choices=["whisper", "aws", "gcp"],
        help="Transcription service to use",
    )
    p.add_argument(
        "--language",
        default=None,
        help="Hint language code (e.g. 'sv', 'en-US') where supported",
    )
    # AWS overrides
    p.add_argument("--aws-bucket", default=None, help="AWS S3 bucket for Transcribe input/output")
    p.add_argument("--aws-region", default=None, help="AWS region for Transcribe (overrides AWS_REGION)")
    # Language detection toggle
    p.add_argument(
        "--auto-language",
        action="store_true",
        help="Enable language auto-detection when supported (AWS).",
    )
    p.add_argument(
        "--aws-language-options",
        default=None,
        help="AWS: comma-separated LanguageOptions (e.g. 'sv-SE,en-US') when using --auto-language",
    )
    # GCP alternative languages (comma-separated)
    p.add_argument(
        "--gcp-alt-languages",
        default=None,
        help="Comma-separated list of alternative language codes for GCP (used if provided)",
    )
    p.add_argument("--output", default=None, help="Output file path; defaults to stdout")
    p.add_argument(
        "--format",
        default=None,
        choices=[
            "txt",
            "pdf",
            "epub",
            "mobi",
            "azw",
            "azw3",
            "kfx",
        ],
        help="Output format. If not provided, inferred from --output extension or defaults to txt.",
    )
    p.add_argument("--title", default=None, help="Document title metadata (for EPUB/PDF/Kindle)")
    p.add_argument("--author", default=None, help="Author metadata (for EPUB/PDF/Kindle)")
    p.add_argument("--cover-image", default=None, help="Cover image path for EPUB/Kindle exports")
    # PDF options
    p.add_argument("--pdf-font", default="Arial", help="PDF font family (default: Arial)")
    p.add_argument("--pdf-font-size", type=int, default=12, help="PDF font size (default: 12)")
    p.add_argument("--pdf-margin", type=int, default=15, help="PDF margin in mm (default: 15)")
    p.add_argument(
        "--pdf-page-size",
        choices=["A4", "Letter"],
        default="A4",
        help="PDF page size (A4 or Letter)",
    )
    p.add_argument(
        "--pdf-orientation",
        choices=["portrait", "landscape"],
        default="portrait",
        help="PDF page orientation",
    )
    p.add_argument(
        "--pdf-font-file",
        default=None,
        help="Embed a TrueType/OpenType font file for Unicode text",
    )
    p.add_argument(
        "--pdf-cover-fullpage",
        action="store_true",
        help="Render the cover image as a dedicated full-page before the transcript",
    )
    p.add_argument(
        "--pdf-first-page-cover-only",
        action="store_true",
        help="Do not mix text on the cover page; start transcript on a new page",
    )
    # EPUB options
    p.add_argument("--epub-css-file", default=None, help="Path to a CSS file to embed in EPUB/Kindle")
    from .exporters.themes import list_themes
    p.add_argument(
        "--epub-theme",
        choices=list_themes(),
        default=None,
        help="Built-in EPUB CSS theme to apply.",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    # Resolve local path (download if URL)
    local_path = ensure_local_audio(args.url)

    # Default service via registry (keeps tests/monkeypatch simple)
    service = services.get_service(args.service)
    # Override with configured instances when flags are provided for cloud backends
    if args.service == "aws" and (args.aws_bucket or args.aws_region or args.auto_language or args.aws_language_options):
        lang_opts = (
            [s.strip() for s in args.aws_language_options.split(",") if s.strip()]
            if args.aws_language_options
            else None
        )
        service = services.AWSTranscribeService(
            bucket=args.aws_bucket,
            region=args.aws_region,
            identify_language=args.auto_language,
            language_options=lang_opts,
        )
    elif args.service == "gcp" and args.gcp_alt_languages:
        alt_langs = [s.strip() for s in args.gcp_alt_languages.split(",") if s.strip()]
        service = services.GCPSpeechService(alternative_language_codes=alt_langs)

    try:
        text = service.transcribe(local_path, language=args.language)
    finally:
        # Clean up temp file if it was created during download
        if getattr(local_path, "_is_temp", False):
            try:
                Path(local_path).unlink(missing_ok=True)
            except Exception:
                pass

    # Decide on output behavior
    from .exporters import export_transcript, infer_format_from_path

    requested_fmt = args.format or infer_format_from_path(args.output) or "txt"

    if requested_fmt != "txt" and not args.output:
        raise SystemExit(
            "--output is required when --format is not 'txt' (binary formats cannot be printed to stdout)."
        )

    if args.output:
        theme_css = None
        if args.epub_theme:
            if isinstance(args.epub_theme, str) and args.epub_theme.startswith("custom:"):
                path = args.epub_theme.split(":", 1)[1]
                theme_css = Path(path).read_text(encoding="utf-8")
            else:
                from .exporters.themes import get_theme_css
                theme_css = get_theme_css(args.epub_theme)
        export_transcript(
            text,
            args.output,
            requested_fmt,
            title=args.title,
            author=args.author,
            cover_image=args.cover_image,
            pdf_font=args.pdf_font,
            pdf_font_size=args.pdf_font_size,
            pdf_margin=args.pdf_margin,
            pdf_page_size=args.pdf_page_size,
            pdf_orientation=args.pdf_orientation,
            pdf_font_file=args.pdf_font_file,
            epub_css_file=args.epub_css_file,
            epub_css_text=theme_css,
            pdf_cover_fullpage=args.pdf_cover_fullpage,
            pdf_first_page_cover_only=args.pdf_first_page_cover_only,
        )
    else:
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
