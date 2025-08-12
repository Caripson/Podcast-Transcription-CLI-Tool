import argparse
import sys
from pathlib import Path

from . import services
from .utils.downloader import ensure_local_audio

try:  # Resolve package version for --version output
    from importlib.metadata import version as _pkg_version  # py3.8+
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="podcast-transcriber",
        description="Transcribe a podcast audio from a URL or file using pluggable services.",
    )
    # Provide a rich --version that includes credits
    ver = "dev"
    if _pkg_version is not None:
        try:
            ver = _pkg_version("podcast-transcriber")
        except Exception:
            ver = "dev"
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {ver} — Developed by Johan Caripson",
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
        choices=["txt","pdf","epub","mobi","azw","azw3","kfx","srt","vtt","json","md"],
        help="Output format. If not provided, inferred from --output extension or defaults to txt.",
    )
    p.add_argument("--title", default=None, help="Document title metadata (for EPUB/PDF/Kindle)")
    p.add_argument("--author", default=None, help="Author metadata (for EPUB/PDF/Kindle)")
    # Utility
    p.add_argument("--credits", action="store_true", help="Show maintainer credits and exit")
    p.add_argument("--cover-image", default=None, help="Cover image path for EPUB/Kindle exports")
    p.add_argument("--auto-toc", action="store_true", help="Generate a simple TOC (PDF/EPUB) from segments if available")
    # Diarization
    p.add_argument("--speakers", type=int, default=None, help="Enable speaker diarization with up to N speakers (AWS/GCP)")
    # Whisper extras
    p.add_argument("--chunk-seconds", type=int, default=None, help="Split long audio for Whisper into N-second chunks")
    p.add_argument("--translate", action="store_true", help="Use Whisper translate task (to English)")
    # Batch and config
    p.add_argument("--input-file", default=None, help="Path to a text file with URLs/paths to process one per line")
    p.add_argument("--config", default=None, help="Path to a TOML config file with default arguments")
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    p.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    # Post-processing
    p.add_argument("--normalize", action="store_true", help="Normalize whitespace and paragraphs in output text")
    p.add_argument("--summarize", type=int, default=None, help="Summarize to N sentences (naive)")
    # Cache
    p.add_argument("--cache-dir", default=None, help="Directory for transcript cache (default: ~/.cache/podcast_transcriber)")
    p.add_argument("--no-cache", action="store_true", help="Disable transcript cache lookup/save")
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
    # EPUB theme selection; allow built-ins or custom:/path.css
    p.add_argument(
        "--epub-theme",
        default=None,
        help="Built-in EPUB CSS theme (see docs) or 'custom:/path/to/file.css'",
    )
    # Whisper options
    p.add_argument(
        "--whisper-model",
        default=None,
        help="Whisper model size (e.g. base, small, medium, large)",
    )
    # AWS housekeeping
    p.add_argument(
        "--aws-keep",
        action="store_true",
        help="Do not delete uploaded S3 object after AWS Transcribe job completes",
    )
    # GCP advanced
    p.add_argument("--gcp-longrunning", action="store_true", help="Use long_running_recognize for long audio (GCP)")
    return p


def _load_config(path: str) -> dict:
    try:
        import tomllib  # py311+
    except Exception:
        try:
            import tomli as tomllib  # type: ignore
        except Exception:
            return {}
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return {}
    return tomllib.loads(p.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # Early utility action before enforcing required args
    if "--credits" in argv:
        sys.stdout.write("Podcast Transcription CLI Tool — Developed by Johan Caripson\n")
        return 0
    args = build_parser().parse_args(argv)
    # Config defaults
    if args.config:
        cfg = _load_config(args.config)
        # Only fill missing simple scalars
        for key in [
            "language","aws_bucket","aws_region","aws_language_options","gcp_alt_languages",
            "format","title","author","cover_image","epub_css_file","epub_theme",
            "whisper_model","chunk_seconds","translate","speakers","aws_keep",
        ]:
            if getattr(args, key.replace("-","_"), None) in (None, False):
                if key in cfg:
                    setattr(args, key.replace("-","_"), cfg[key])

    # Downloader verbosity
    if args.verbose:
        import os as _os
        _os.environ["PODCAST_TRANSCRIBER_VERBOSE"] = "1"
    # Resolve local path (download if URL)
    local_path = ensure_local_audio(args.url)

    # Default service via registry (keeps tests/monkeypatch simple)
    service = services.get_service(args.service)
    # Respect monkeypatched/custom services in tests by only tweaking
    # configuration if the instance is of the expected type.
    if args.service == "whisper" and isinstance(service, services.WhisperService):
        if args.whisper_model:
            service.model_name = args.whisper_model
        service.translate = bool(args.translate)
        service.chunk_seconds = args.chunk_seconds
    elif args.service == "aws" and isinstance(service, services.AWSTranscribeService) and (
        args.aws_bucket or args.aws_region or args.auto_language or args.aws_language_options or args.aws_keep or args.speakers
    ):
        lang_opts = (
            [s.strip() for s in args.aws_language_options.split(",") if s.strip()]
            if args.aws_language_options
            else None
        )
        # Re-create with provided overrides to keep constructor validation
        service = services.AWSTranscribeService(
            bucket=args.aws_bucket,
            region=args.aws_region,
            identify_language=args.auto_language,
            language_options=lang_opts,
            keep=args.aws_keep,
            speakers=args.speakers,
        )
    elif args.service == "gcp" and isinstance(service, services.GCPSpeechService):
        alt_langs = (
            [s.strip() for s in args.gcp_alt_languages.split(",") if s.strip()]
            if args.gcp_alt_languages
            else None
        )
        # Update attributes only when using the default implementation
        service.alternative_language_codes = alt_langs
        service.speakers = args.speakers
        service.long_running = bool(args.gcp_longrunning)

    try:
        # Batch mode
        if args.input_file:
            from .exporters import export_transcript
            srcs = [s.strip() for s in Path(args.input_file).read_text(encoding="utf-8").splitlines() if s.strip()]
            if not args.output:
                raise SystemExit("--output directory is required for --input-file batch mode")
            out_dir = Path(args.output)
            out_dir.mkdir(parents=True, exist_ok=True)
            for src in srcs:
                lp = ensure_local_audio(src)
                txt = service.transcribe(lp, language=args.language)
                segs = getattr(service, "last_segments", None)
                words = getattr(service, "last_words", None)
                name = Path(src).stem or "item"
                fmt = args.format or infer_format_from_path(str(args.output)) or "txt"
                out_path = out_dir / f"{name}.{fmt}"
                export_transcript(
                    txt,
                    str(out_path),
                    fmt,
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
                    epub_css_text=None,
                    pdf_cover_fullpage=args.pdf_cover_fullpage,
                    pdf_first_page_cover_only=args.pdf_first_page_cover_only,
                    segments=segs,
                    words=words,
                )
            return 0

        # Simple cache lookup for single-file mode
        text = None
        cache_key = None
        if not args.input_file and not args.no_cache:
            try:
                from .utils import cache as _cache
                cache_key = _cache.compute_key(
                    source=args.url,
                    service=args.service,
                    opts=tuple(filter(None, [
                        str(args.language or ""), str(args.speakers or 0), str(args.whisper_model or ""),
                        "translate" if args.translate else "", str(args.chunk_seconds or 0)
                    ])),
                    local_path=str(local_path),
                )
                payload = _cache.get(args.cache_dir, cache_key)
                if payload and "text" in payload:
                    text = payload["text"]
                    setattr(service, "last_segments", payload.get("segments"))
                    setattr(service, "last_words", payload.get("words"))
            except Exception:
                text = None
        if text is None:
            text = service.transcribe(local_path, language=args.language)
            if cache_key and not args.no_cache:
                try:
                    from .utils import cache as _cache
                    payload = {
                        "text": text,
                        "segments": getattr(service, "last_segments", None),
                        "words": getattr(service, "last_words", None),
                    }
                    _cache.set(args.cache_dir, cache_key, payload)
                except Exception:
                    pass
    finally:
        # Clean up temp file if it was created during download
        if bool(getattr(local_path, "is_temp", False) or getattr(local_path, "_is_temp", False)):
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

    # Post-processing
    if args.normalize:
        from .utils.textproc import normalize_text as _norm
        text = _norm(text)
    if args.summarize:
        from .utils.textproc import summarize_text as _sum
        text = _sum(text, max_sentences=int(args.summarize))

    if args.output:
        theme_css = None
        if args.epub_theme:
            if isinstance(args.epub_theme, str) and args.epub_theme.startswith("custom:"):
                path = args.epub_theme.split(":", 1)[1]
                theme_css = Path(path).read_text(encoding="utf-8")
            else:
                from .exporters.themes import get_theme_css, list_themes
                if args.epub_theme not in list_themes():
                    raise SystemExit(
                        f"Unknown EPUB theme '{args.epub_theme}'. Available: {', '.join(list_themes())} or use custom:/path.css"
                    )
                theme_css = get_theme_css(args.epub_theme)
        segs = getattr(service, "last_segments", None)
        words = getattr(service, "last_words", None)
        # Auto-fill metadata: title/cover
        eff_title = args.title
        cover_bytes = None
        if not eff_title:
            for attr in ("id3_title", "source_title"):
                t = getattr(local_path, attr, None)
                if t:
                    eff_title = t
                    break
        if not args.cover_image:
            cover_bytes = getattr(local_path, "cover_image_bytes", None)
            if not cover_bytes:
                cover_url = getattr(local_path, "cover_url", None)
                if cover_url:
                    try:
                        import requests as _rq
                        r = _rq.get(cover_url, timeout=20)
                        r.raise_for_status()
                        cover_bytes = r.content
                    except Exception:
                        cover_bytes = None

        export_transcript(
            text,
            args.output,
            requested_fmt,
            title=eff_title,
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
            segments=segs,
            words=words,
            auto_toc=bool(args.auto_toc),
            pdf_header=(eff_title or None),
            pdf_footer=(args.author or ""),
            cover_image_bytes=cover_bytes,
        )
    else:
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
