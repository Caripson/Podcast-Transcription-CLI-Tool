import argparse
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

from .storage.state import StateStore
from .ingestion.feed import discover_new_episodes
from .utils.downloader import ensure_local_audio
from . import services
from .exporters import export_book
from .utils.textproc import normalize_text, summarize_text
from .kindle.epub_builder import Document, Chapter
from .templates.render import render_markdown
from .nlp.segment_topics import segment_with_embeddings, key_takeaways_better
from typing import Optional, Dict
from .delivery.send_to_kindle import send_file_via_smtp


def load_yaml_config(path: str) -> dict:
    try:
        import yaml  # type: ignore
    except Exception as e:
        raise SystemExit("PyYAML is required for --config. Install with: pip install pyyaml") from e
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Config file not found: {path}")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def pick_quality_settings(quality: str) -> dict:
    q = (quality or "standard").lower()
    if q in ("quick", "snabb", "fast"):
        return {"whisper_model": "base", "diarization": 0, "summarize": False, "chapter_minutes": None}
    if q in ("premium",):
        return {"whisper_model": "large", "diarization": 2, "summarize": True, "chapter_minutes": None, "translate": False, "topic_segmentation": True}
    # default: standard
    return {"whisper_model": "small", "diarization": 0, "summarize": True, "chapter_minutes": 10}


def cmd_ingest(args) -> int:
    cfg = load_yaml_config(args.config)
    store = StateStore()
    eps = discover_new_episodes(cfg, store)
    # Filter by feed name if provided
    if args.feed:
        eps = [e for e in eps if e.get("feed") == args.feed]
    if not eps:
        print("No new episodes discovered.")
        return 0
    job = store.create_job_with_episodes(cfg, eps)
    print(job["id"])  # Emit job id for chaining
    return 0


def _process_episode(ep: dict, service_name: str, quality: str, language: Optional[str], nlp_cfg: Optional[Dict] = None) -> dict:
    qs = pick_quality_settings(quality)
    service = services.get_service(service_name)
    if service_name == "whisper" and getattr(services, "WhisperService", None) is not None and isinstance(service, services.WhisperService):
        service.model_name = qs.get("whisper_model") or getattr(service, "model_name", None)
        service.translate = bool(qs.get("translate", False))
    if qs.get("diarization", 0) and service_name in ("aws", "gcp"):
        try:
            setattr(service, "speakers", int(qs["diarization"]))
        except Exception:
            pass
    local_path = ensure_local_audio(ep["source"])  # URL or path
    text = service.transcribe(local_path, language=language)
    segs = getattr(service, "last_segments", None)
    # normalize optionally
    text = normalize_text(text)
    # basic summaries for standard/premium
    summary = None
    if qs.get("summarize"):
        summary = summarize_text(text, max_sentences=6)
    # basic chapterization by minutes when segments available
    chapters = []
    # NLP: semantic topic segmentation when configured
    use_semantic = bool((nlp_cfg or {}).get("semantic")) or bool(qs.get("topic_segmentation"))
    if use_semantic:
        try:
            topics = segment_with_embeddings(text)
            chapters = [{"title": t["title"], "text": t["text"]} for t in topics]
        except Exception:
            chapters = []
    if not chapters and qs.get("chapter_minutes") and segs:
        mins = int(qs["chapter_minutes"]) or 10
        bucket = []
        bucket_chars = 0
        start_time = None
        for s in segs:
            if start_time is None:
                start_time = s.get("start", 0.0)
            bucket.append(s.get("text", ""))
            bucket_chars += len(bucket[-1])
            if (s.get("end", 0.0) - start_time) >= mins * 60 or bucket_chars > 4000:
                chapters.append({"title": f"Chapter {len(chapters)+1}", "text": " ".join(bucket)})
                bucket, bucket_chars, start_time = [], 0, None
        if bucket:
            chapters.append({"title": f"Chapter {len(chapters)+1}", "text": " ".join(bucket)})
    else:
        chapters = [{"title": ep.get("title") or "Transcript", "text": text}]
    # Enrich with key takeaways if NLP enabled
    if (nlp_cfg or {}).get("takeaways"):
        try:
            kt = key_takeaways_better(text)
            if kt:
                takeaways = kt
            else:
                takeaways = None
        except Exception:
            takeaways = None
    else:
        takeaways = None
    return {"text": text, "chapters": chapters, "summary": summary, "takeaways": takeaways}


def cmd_process(args) -> int:
    store = StateStore()
    job = store.get_job(args.job_id)
    if not job:
        raise SystemExit(f"Unknown job id: {args.job_id}")
    cfg = job.get("config") or {}
    service_name = cfg.get("service", "whisper")
    quality = cfg.get("quality", "standard")
    language = cfg.get("language")
    out_dir = Path(cfg.get("output_dir", "./out"))
    out_dir.mkdir(parents=True, exist_ok=True)
    processed = []
    bilingual = bool(cfg.get("bilingual"))
    translation_lang = cfg.get("translation_language") or "en"
    nlp_cfg = cfg.get("nlp") or {}
    if getattr(args, "semantic", False):
        nlp_cfg = dict(nlp_cfg)
        nlp_cfg["semantic"] = True
    emit_md = bool(cfg.get("emit_markdown"))
    md_template = cfg.get("markdown_template") or str(Path(__file__).resolve().parent / "templates" / "ebook.md.j2")
    for ep in job.get("episodes", []):
        res = _process_episode(ep, service_name, quality, language, nlp_cfg=nlp_cfg)
        # Build document
        title = ep.get("title") or job.get("title") or "Podcast Transcript"
        author = cfg.get("author")
        cover_image = cfg.get("cover_image")
        chapters = [Chapter(c["title"], c["text"]) for c in res["chapters"]]
        if bilingual and service_name == "whisper":
            try:
                svc_tr = services.get_service("whisper")
                if getattr(services, "WhisperService", None) is not None and isinstance(svc_tr, services.WhisperService):
                    svc_tr.translate = True
                text_tr = svc_tr.transcribe(ensure_local_audio(ep["source"]))
                chapters = [Chapter("Original", "\n\n".join(c.text for c in chapters)), Chapter("Translated", text_tr)]
            except Exception:
                pass
        doc = Document(title=title, author=author, chapters=chapters, summary=res.get("summary"))
        out_path = out_dir / f"{Path(ep.get('slug') or title).stem}.epub"
        export_book(
            chapters=[{"title": ch.title, "text": ch.text} for ch in doc.chapters],
            out_path=str(out_path),
            fmt="epub",
            title=doc.title,
            author=doc.author,
            cover_image=cover_image,
            metadata={
                "language": language,
                "description": cfg.get("description"),
                "keywords": cfg.get("keywords"),
            },
        )
        # Optional: emit companion Markdown using Jinja2 template
        if emit_md:
            md_path = out_path.with_suffix('.md')
            try:
                md_text = render_markdown(md_template, {
                    "title": doc.title,
                    "author": doc.author,
                    "summary": doc.summary,
                    "topics": [ch.title for ch in doc.chapters],
                    "takeaways": res.get("takeaways"),
                    "chapters": [{"title": ch.title, "text": ch.text} for ch in doc.chapters],
                })
            except Exception:
                # Fallback: minimal Markdown without Jinja2 dependency
                lines = []
                if doc.title:
                    lines += [f"# {doc.title}", ""]
                if doc.author:
                    lines += [f"_by {doc.author}_", ""]
                if doc.summary:
                    lines += ["## Summary", "", str(doc.summary), ""]
                topics = [ch.title for ch in doc.chapters]
                if topics:
                    lines += ["## Topics", ""]
                    lines += ["- " + t for t in topics]
                    lines += [""]
                takeaways = res.get("takeaways")
                if takeaways:
                    lines += ["## Key Takeaways", ""]
                    lines += ["- " + k for k in takeaways]
                    lines += [""]
                for ch in doc.chapters:
                    lines += [f"## {ch.title}", "", ch.text, ""]
                md_text = "\n".join(lines).rstrip() + "\n"
            md_path.write_text(md_text, encoding='utf-8')
        processed.append({"episode": ep, "output": str(out_path)})
    job["artifacts"] = processed
    job["status"] = "processed"
    store.save_job(job)
    print(str([p["output"] for p in processed]))
    return 0


def cmd_send(args) -> int:
    store = StateStore()
    job = store.get_job(args.job_id)
    if not job:
        raise SystemExit(f"Unknown job id: {args.job_id}")
    to_email = job.get("config", {}).get("kindle", {}).get("to_email") or os.environ.get("KINDLE_TO_EMAIL")
    from_email = job.get("config", {}).get("kindle", {}).get("from_email") or os.environ.get("KINDLE_FROM_EMAIL")
    if not to_email or not from_email:
        raise SystemExit("Missing Kindle to/from email. Set in config.yml under kindle or via env KINDLE_TO_EMAIL/KINDLE_FROM_EMAIL")
    smtp_cfg = job.get("config", {}).get("smtp", {})
    host = smtp_cfg.get("host") or os.environ.get("SMTP_HOST")
    port = int(smtp_cfg.get("port") or os.environ.get("SMTP_PORT") or 587)
    user = smtp_cfg.get("user") or os.environ.get("SMTP_USER")
    # Enforce password via env var only for safety
    password = os.environ.get(smtp_cfg.get("pass_env", "SMTP_PASS"))
    if not host or not user or not password:
        raise SystemExit("SMTP credentials missing. Provide SMTP_HOST, SMTP_PORT, SMTP_USER and SMTP_PASS (or pass_env) env vars.")
    artifacts = job.get("artifacts", [])
    if not artifacts:
        raise SystemExit("No artifacts to send. Run process first.")
    sent = []
    for art in artifacts:
        path = art.get("output")
        send_file_via_smtp(
            smtp_host=host,
            smtp_port=port,
            smtp_user=user,
            smtp_password=password,
            from_email=from_email,
            to_email=to_email,
            subject=os.path.basename(path),
            body="Sent via podcast-cli",
            attachment_path=path,
        )
        sent.append(path)
    job["status"] = "sent"
    store.save_job(job)
    print(str(sent))
    return 0


def cmd_run(args) -> int:
    # Convenience: ingest -> process -> send
    cfg = load_yaml_config(args.config)
    store = StateStore()
    job = store.create_job(cfg)
    args2 = argparse.Namespace(job_id=job["id"])
    cmd_process(args2)
    cmd_send(args2)
    return 0


def cmd_digest(args) -> int:
    # Placeholder weekly digest: gather episodes processed in last 7 days and merge into one book
    store = StateStore()
    recent = store.list_recent(days=7, feed_name=args.feed)
    if not recent:
        print("No recent episodes found for digest.")
        return 0
    chapters = []
    for ep in recent:
        text = ep.get("last_text") or "(no transcript cached)"
        chapters.append({"title": ep.get("title") or ep.get("slug") or "Episode", "text": text})
    out_dir = Path("./out")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"digest-{datetime.utcnow().date()}.epub"
    export_book(chapters, str(out_path), fmt="epub", title=f"{args.feed or 'Podcast'} Weekly Digest")
    print(str(out_path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="podcast-cli", description="Orchestrates podcast ingestion → EPUB → Kindle delivery")
    sub = p.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingest", help="Discover new episodes and create a job")
    ing.add_argument("--config", required=True, help="Path to YAML config")
    ing.add_argument("--feed", default=None, help="Optional feed name to limit ingestion")
    ing.set_defaults(func=cmd_ingest)

    proc = sub.add_parser("process", help="Transcribe and build EPUB for a job")
    proc.add_argument("--job-id", required=True)
    proc.add_argument("--semantic", action="store_true", help="Enable semantic topic segmentation for this run")
    proc.set_defaults(func=cmd_process)

    snd = sub.add_parser("send", help="Email EPUB to Kindle for a job")
    snd.add_argument("--job-id", required=True)
    snd.set_defaults(func=cmd_send)

    run = sub.add_parser("run", help="Run ingest→process→send for new episodes")
    run.add_argument("--config", required=True)
    run.set_defaults(func=cmd_run)

    dig = sub.add_parser("digest", help="Build a weekly digest EPUB")
    dig.add_argument("--feed", default=None)
    dig.add_argument("--weekly", action="store_true")
    dig.set_defaults(func=cmd_digest)

    return p


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # Load .env if python-dotenv is available (optional convenience)
    try:
        import dotenv  # type: ignore
        dotenv.load_dotenv()  # loads from .env in CWD if present
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
