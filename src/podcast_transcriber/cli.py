import argparse
import sys
from pathlib import Path
from typing import Optional

from . import __credits__, __version__, services
from .utils.downloader import ensure_local_audio


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="podcast-transcriber",
        description="Transcribe a podcast audio from a URL or file using pluggable services.",
    )
    # Provide a rich --version that includes credits
    ver = __version__
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {ver} — {__credits__}",
    )
    # URL/File may be provided interactively; not required here
    p.add_argument("--url", default=None, help="Audio URL or local file path")
    p.add_argument(
        "--service",
        default=None,
        choices=services.list_service_names(),
        help="Transcription service to use",
    )
    p.add_argument(
        "--language",
        default=None,
        help="Hint language code (e.g. 'sv', 'en-US') where supported",
    )
    # AWS overrides
    p.add_argument(
        "--aws-bucket", default=None, help="AWS S3 bucket for Transcribe input/output"
    )
    p.add_argument(
        "--aws-region",
        default=None,
        help="AWS region for Transcribe (overrides AWS_REGION)",
    )
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
    p.add_argument(
        "--output", default=None, help="Output file path; defaults to stdout"
    )
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
            "srt",
            "vtt",
            "json",
            "md",
        ],
        help="Output format. If not provided, inferred from --output extension or defaults to txt.",
    )
    p.add_argument(
        "--title", default=None, help="Document title metadata (for EPUB/PDF/Kindle)"
    )
    p.add_argument(
        "--author", default=None, help="Author metadata (for EPUB/PDF/Kindle)"
    )
    # KDP-oriented metadata
    p.add_argument("--subtitle", default=None, help="Subtitle (KDP/EPUB metadata)")
    p.add_argument(
        "--description", default=None, help="Long description/blurb (KDP/EPUB metadata)"
    )
    p.add_argument(
        "--keywords", default=None, help="Comma-separated keywords (KDP/EPUB metadata)"
    )
    p.add_argument("--series-title", default=None, help="Series title (KDP metadata)")
    p.add_argument(
        "--volume-number",
        type=str,
        default=None,
        help="Series volume number (KDP metadata)",
    )
    # Utility
    p.add_argument(
        "--credits", action="store_true", help="Show maintainer credits and exit"
    )
    p.add_argument(
        "--cover-image", default=None, help="Cover image path for EPUB/Kindle exports"
    )
    p.add_argument(
        "--auto-toc",
        action="store_true",
        help="Generate a simple TOC (PDF/EPUB) from segments if available",
    )
    # Diarization
    p.add_argument(
        "--speakers",
        type=int,
        default=None,
        help="Enable speaker diarization with up to N speakers (AWS/GCP)",
    )
    # Whisper extras
    p.add_argument(
        "--chunk-seconds",
        type=int,
        default=None,
        help="Split long audio for Whisper into N-second chunks",
    )
    p.add_argument(
        "--translate",
        action="store_true",
        help="Use Whisper translate task (to English)",
    )
    # Batch and config
    p.add_argument(
        "--input-file",
        default=None,
        help="Path to a text file with URLs/paths to process one per line",
    )
    p.add_argument(
        "--combine-into",
        default=None,
        help="Combine all inputs into a single book at this output path (requires --input-file)",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Path to a TOML config file with default arguments (auto-discovers in ~/.config/podcast-transcriber/config.toml)",
    )
    p.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode: guided prompts for common options",
    )
    p.add_argument(
        "--kdp",
        action="store_true",
        help="Enable KDP pipeline defaults (normalize, EPUB with TOC, metadata)",
    )
    p.add_argument("--verbose", action="store_true", help="Verbose output")
    p.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    # Post-processing
    p.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize whitespace and paragraphs in output text",
    )
    p.add_argument(
        "--summarize", type=int, default=None, help="Summarize to N sentences (naive)"
    )
    # Cache
    p.add_argument(
        "--cache-dir",
        default=None,
        help="Directory for transcript cache (default: ~/.cache/podcast_transcriber)",
    )
    p.add_argument(
        "--no-cache", action="store_true", help="Disable transcript cache lookup/save"
    )
    # PDF options
    p.add_argument(
        "--pdf-font", default="Arial", help="PDF font family (default: Arial)"
    )
    p.add_argument(
        "--pdf-font-size", type=int, default=12, help="PDF font size (default: 12)"
    )
    p.add_argument(
        "--pdf-margin", type=int, default=15, help="PDF margin in mm (default: 15)"
    )
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
    p.add_argument(
        "--epub-css-file",
        default=None,
        help="Path to a CSS file to embed in EPUB/Kindle",
    )
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
    p.add_argument(
        "--gcp-longrunning",
        action="store_true",
        help="Use long_running_recognize for long audio (GCP)",
    )
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


def _discover_default_config() -> Optional[str]:
    # Priority: env var, XDG, ~/.config, legacy home file
    import os

    env = os.environ.get("PODCAST_TRANSCRIBER_CONFIG")
    if env and Path(env).exists():
        return env
    xdg = os.environ.get("XDG_CONFIG_HOME")
    candidates = []
    if xdg:
        candidates.append(Path(xdg) / "podcast-transcriber" / "config.toml")
    home = Path.home()
    candidates.append(home / ".config" / "podcast-transcriber" / "config.toml")
    candidates.append(home / ".podcast_transcriber.toml")
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def _interactive_fill_args(args: argparse.Namespace) -> None:
    # Small helper to prompt user for missing essentials
    def _inp(prompt: str, default: Optional[str] = None) -> str:
        suffix = f" [{default}]" if default else ""
        val = input(f"{prompt}{suffix}: ").strip()
        return val or (default or "")

    if not args.url:
        args.url = _inp("Which file/URL do you want to transcribe?")
    # Choose service
    available = services.list_service_names()
    if not args.service or args.service not in available:
        print("Available services:")
        for i, name in enumerate(available, start=1):
            print(f"  {i}. {name}")
        sel = _inp("Which service do you want to use? (name or number)")
        try:
            idx = int(sel)
            if 1 <= idx <= len(available):
                args.service = available[idx - 1]
        except Exception:
            if sel in available:
                args.service = sel
    # Format
    from .exporters.exporter import SUPPORTED_FORMATS

    if not args.format:
        print(f"Available formats: {', '.join(sorted(SUPPORTED_FORMATS))}")
        args.format = _inp("Which output format do you want?", default="txt")
        if args.format not in SUPPORTED_FORMATS:
            print("Okänt format, använder 'txt'.")
            args.format = "txt"
    # Output path
    if args.format != "txt" and not args.output:
        args.output = _inp("Output file path? (required for non-txt)")
    elif args.format == "txt" and not args.output:
        args.output = (
            _inp("Output file path? (empty = write to stdout)", default="") or None
        )
    # Language optional
    if not args.language:
        lang = _inp("Language code? (e.g., sv, en-US)", default="")
        args.language = lang or None


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # Early utility action before enforcing required args
    if "--credits" in argv:
        sys.stdout.write(
            "Podcast Transcription CLI Tool — Developed by Johan Caripson\n"
        )
        return 0
    args = build_parser().parse_args(argv)
    # If interactive, collect essentials before validation
    if args.interactive:
        _interactive_fill_args(args)
    # Config defaults (explicit or discovered)
    cfg_path = args.config or _discover_default_config()
    if cfg_path:
        cfg = _load_config(cfg_path)
        # Only fill missing simple scalars
        for key in [
            "language",
            "aws_bucket",
            "aws_region",
            "aws_language_options",
            "gcp_alt_languages",
            "format",
            "title",
            "subtitle",
            "author",
            "description",
            "keywords",
            "cover_image",
            "epub_css_file",
            "epub_theme",
            "series_title",
            "volume_number",
            "whisper_model",
            "chunk_seconds",
            "translate",
            "speakers",
            "aws_keep",
        ]:
            if getattr(args, key.replace("-", "_"), None) in (None, False):
                if key in cfg:
                    setattr(args, key.replace("-", "_"), cfg[key])
        # If URL/service still missing and config provides them, pick up
        for key in ["url", "service", "output"]:
            if getattr(args, key, None) in (None, "") and key in cfg:
                setattr(args, key, cfg[key])

    # Validate essentials unless interactive already ensured them
    # Allow batch mode (--input-file) without --url
    if not args.url and not args.input_file:
        raise SystemExit("--url is required (or use --interactive)")
    if not args.service:
        raise SystemExit("--service is required (or use --interactive)")

    # Downloader verbosity
    if args.verbose:
        import os as _os

        _os.environ["PODCAST_TRANSCRIBER_VERBOSE"] = "1"

    # KDP pipeline defaults
    if args.kdp:
        if not args.format:
            args.format = "epub"
        args.normalize = (
            True if not getattr(args, "normalize", False) else args.normalize
        )
        args.auto_toc = True if not getattr(args, "auto_toc", False) else args.auto_toc
    # Prepare for optional single-file download path
    # In batch mode (--input-file), we resolve per-item later.
    local_path = None

    # Default service via registry (keeps tests/monkeypatch simple)
    service = services.get_service(args.service)
    # Respect monkeypatched/custom services in tests by only tweaking
    # configuration if the instance is of the expected type.
    if (
        args.service == "whisper"
        and getattr(services, "WhisperService", None) is not None
        and isinstance(service, services.WhisperService)
    ):
        if args.whisper_model:
            service.model_name = args.whisper_model
        service.translate = bool(args.translate)
        service.chunk_seconds = args.chunk_seconds
    elif (
        args.service == "aws"
        and getattr(services, "AWSTranscribeService", None) is not None
        and isinstance(service, services.AWSTranscribeService)
        and (
            args.aws_bucket
            or args.aws_region
            or args.auto_language
            or args.aws_language_options
            or args.aws_keep
            or args.speakers
        )
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
    elif (
        args.service == "gcp"
        and getattr(services, "GCPSpeechService", None) is not None
        and isinstance(service, services.GCPSpeechService)
    ):
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
            from .exporters import (
                export_book,
                export_transcript,
                infer_format_from_path,
            )

            srcs = [
                s.strip()
                for s in Path(args.input_file).read_text(encoding="utf-8").splitlines()
                if s.strip()
            ]
            # Combine all into a single book
            if args.combine_into:
                chapters = []
                cover_bytes = None
                for src in srcs:
                    lp = ensure_local_audio(src)
                    txt = service.transcribe(lp, language=args.language)
                    if args.normalize:
                        from .utils.textproc import normalize_text as _norm

                        txt = _norm(txt)
                    # Title for chapter
                    ch_title = (
                        getattr(lp, "id3_title", None)
                        or getattr(lp, "source_title", None)
                        or Path(src).stem
                    )
                    chapters.append({"title": ch_title, "text": txt})
                    if not args.cover_image and cover_bytes is None:
                        cover_bytes = getattr(lp, "cover_image_bytes", None)
                        if not cover_bytes:
                            cover_url = getattr(lp, "cover_url", None)
                            if cover_url:
                                try:
                                    import requests as _rq

                                    r = _rq.get(cover_url, timeout=20)
                                    r.raise_for_status()
                                    cover_bytes = r.content
                                except Exception:
                                    cover_bytes = None
                # Determine format from target path
                fmt = args.format or infer_format_from_path(args.combine_into) or "epub"
                # Build metadata payload suitable for EPUB/KDP
                md = {
                    "language": args.language,
                    "description": args.description,
                    "keywords": [
                        s.strip() for s in (args.keywords or "").split(",") if s.strip()
                    ]
                    or None,
                    "series_title": args.series_title,
                    "volume_number": args.volume_number,
                    "subtitle": args.subtitle,
                }
                export_book(
                    chapters,
                    args.combine_into,
                    fmt,
                    title=args.title,
                    author=args.author,
                    cover_image=args.cover_image,
                    cover_image_bytes=cover_bytes,
                    metadata=md,
                    epub_css_file=args.epub_css_file,
                    epub_css_text=None,
                )
            else:
                if not args.output:
                    raise SystemExit(
                        "--output directory is required for --input-file batch mode (or use --combine-into)"
                    )
                out_dir = Path(args.output)
                out_dir.mkdir(parents=True, exist_ok=True)
                for src in srcs:
                    lp = ensure_local_audio(src)
                    txt = service.transcribe(lp, language=args.language)
                    segs = getattr(service, "last_segments", None)
                    words = getattr(service, "last_words", None)
                    if args.normalize:
                        from .utils.textproc import normalize_text as _norm

                        txt = _norm(txt)
                    name = Path(src).stem or "item"
                    fmt = (
                        args.format or infer_format_from_path(str(args.output)) or "txt"
                    )
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

        # Single-file mode: resolve local path (download if URL)
        local_path = ensure_local_audio(args.url)

        # Simple cache lookup for single-file mode
        text = None
        cache_key = None
        if not args.input_file and not args.no_cache:
            try:
                from .utils import cache as _cache

                cache_key = _cache.compute_key(
                    source=args.url,
                    service=args.service,
                    opts=tuple(
                        filter(
                            None,
                            [
                                str(args.language or ""),
                                str(args.speakers or 0),
                                str(args.whisper_model or ""),
                                "translate" if args.translate else "",
                                str(args.chunk_seconds or 0),
                            ],
                        )
                    ),
                    local_path=str(local_path),
                )
                payload = _cache.get(args.cache_dir, cache_key)
                if payload and "text" in payload:
                    text = payload["text"]
                    try:
                        service.last_segments = payload.get("segments")
                        service.last_words = payload.get("words")
                    except Exception:
                        pass
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
        if local_path is not None:
            if bool(
                getattr(local_path, "is_temp", False)
                or getattr(local_path, "_is_temp", False)
            ):
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
            if isinstance(args.epub_theme, str) and args.epub_theme.startswith(
                "custom:"
            ):
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
        # Collect source/download metadata for JSON/EPUB export
        meta = {
            "source_url": args.url,
            "local_path": str(local_path),
        }
        for attr in (
            "id3_title",
            "id3_artist",
            "source_title",
            "source_uploader",
            "cover_url",
        ):
            val = getattr(local_path, attr, None)
            if val:
                meta[attr] = val
        # KDP/EPUB metadata
        if args.language:
            meta["language"] = args.language
        if args.description:
            meta["description"] = args.description
        if args.keywords:
            meta["keywords"] = [
                s.strip() for s in args.keywords.split(",") if s.strip()
            ]
        if args.subtitle:
            meta["subtitle"] = args.subtitle
        if args.series_title:
            meta["series_title"] = args.series_title
        if args.volume_number:
            meta["volume_number"] = args.volume_number
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
            metadata=meta,
        )
    else:
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
