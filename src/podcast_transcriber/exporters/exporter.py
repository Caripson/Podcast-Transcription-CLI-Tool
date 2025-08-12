import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

SUPPORTED_FORMATS = {"txt", "pdf", "epub", "mobi", "azw", "azw3", "kfx"}


def infer_format_from_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    ext = Path(path).suffix.lower().lstrip(".")
    return ext if ext in SUPPORTED_FORMATS else None


def export_transcript(
    text: str,
    out_path: str,
    fmt: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    cover_image: Optional[str] = None,
    pdf_font: str = "Arial",
    pdf_font_size: int = 12,
    pdf_margin: int = 15,
    epub_css_file: Optional[str] = None,
    epub_css_text: Optional[str] = None,
    pdf_cover_fullpage: bool = False,
    pdf_first_page_cover_only: bool = False,
    pdf_page_size: str = "A4",
    pdf_orientation: str = "portrait",
    pdf_font_file: Optional[str] = None,
) -> None:
    fmt = fmt.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {fmt}")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    if fmt == "txt":
        Path(out_path).write_text(text, encoding="utf-8")
        return

    if fmt == "pdf":
        _export_pdf(
            text,
            out_path,
            title=title,
            author=author,
            font=pdf_font,
            font_size=pdf_font_size,
            margin=pdf_margin,
            cover_path=cover_image,
            cover_fullpage=pdf_cover_fullpage,
            page_size=pdf_page_size,
            orientation=pdf_orientation,
            first_page_cover_only=pdf_first_page_cover_only,
            font_file=pdf_font_file,
        )
        return

    if fmt == "epub":
        _export_epub(
            text,
            out_path,
            title=title,
            author=author,
            cover_image=cover_image,
            css_file=epub_css_file,
            css_text=epub_css_text,
        )
        return

    # Kindle family: convert via Calibre's ebook-convert from an EPUB
    _export_kindle(
        text,
        out_path,
        target_fmt=fmt,
        title=title,
        author=author,
        cover_image=cover_image,
        css_file=epub_css_file,
        css_text=epub_css_text,
    )


def _export_pdf(
    text: str,
    out_path: str,
    title: Optional[str],
    author: Optional[str],
    font: str = "Arial",
    font_size: int = 12,
    margin: int = 15,
    cover_path: Optional[str] = None,
    cover_fullpage: bool = False,
    first_page_cover_only: bool = False,
    page_size: str = "A4",
    orientation: str = "portrait",
    font_file: Optional[str] = None,
):
    try:
        from fpdf import FPDF  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "PDF export requires 'fpdf2'. Install with: pip install fpdf2"
        ) from e

    orient_flag = "P" if str(orientation).lower().startswith("p") else "L"
    try:
        pdf = FPDF(orientation=orient_flag, format=page_size)
    except Exception:
        pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=margin)
    pdf.add_page()
    pdf.set_title(title or "Transcript")
    if author:
        pdf.set_author(author)
    # Custom font embedding
    if font_file:
        ff = Path(font_file)
        if not ff.exists():
            raise FileNotFoundError(f"PDF font file not found: {font_file}")
        try:
            if hasattr(pdf, "add_font"):
                pdf.add_font("Embedded", "", str(ff), uni=True)  # type: ignore[arg-type]
                pdf.set_font("Embedded", size=font_size)
            else:
                pdf.set_font(font, size=font_size)
        except Exception:
            # Fallback to built-in font on any failure
            pdf.set_font(font, size=font_size)
    else:
        pdf.set_font(font, size=font_size)
    # Optional cover on first page
    if cover_path:
        p = Path(cover_path)
        if not p.exists():
            raise FileNotFoundError(f"Cover image not found: {cover_path}")
        fd, tmp_cover = tempfile.mkstemp(prefix="cover_", suffix=".jpg")
        os.close(fd)
        try:
            data = _prepare_cover_bytes(p)
            Path(tmp_cover).write_bytes(data)
            if cover_fullpage:
                # Full-page: draw image across page width, minimal margins
                try:
                    page_w = pdf.w  # type: ignore[attr-defined]
                except Exception:
                    page_w = 210  # A4 width mm fallback
                pdf.image(tmp_cover, x=0, y=0, w=page_w)
                # Start transcript on a new page
                pdf.add_page()
            else:
                try:
                    epw = pdf.epw  # type: ignore[attr-defined]
                except Exception:
                    try:
                        epw = pdf.w - 2 * pdf.l_margin  # type: ignore[attr-defined]
                    except Exception:
                        epw = 150
                try:
                    x = pdf.l_margin  # type: ignore[attr-defined]
                except Exception:
                    x = 10
                pdf.image(tmp_cover, x=x, y=None, w=epw)
                pdf.ln(10)
                if first_page_cover_only:
                    pdf.add_page()
        finally:
            try:
                Path(tmp_cover).unlink(missing_ok=True)
            except Exception:
                pass
    # Basic wrapping: split on double newlines as paragraphs
    for para in text.split("\n\n"):
        for line in para.splitlines():
            pdf.multi_cell(0, 8, line)
        pdf.ln(4)
    pdf.output(out_path)


def _export_epub(
    text: str,
    out_path: str,
    title: Optional[str],
    author: Optional[str],
    cover_image: Optional[str] = None,
    css_file: Optional[str] = None,
    css_text: Optional[str] = None,
):
    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "EPUB export requires 'ebooklib'. Install with: pip install ebooklib"
        ) from e

    book = epub.EpubBook()
    book.set_title(title or "Transcript")
    if author:
        book.add_author(author)
    if cover_image:
        p = Path(cover_image)
        if not p.exists():
            raise FileNotFoundError(f"Cover image not found: {cover_image}")
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            raise ValueError("Cover image must be a .jpg, .jpeg or .png file")
        try:
            data = _prepare_cover_bytes(p)  # if Pillow available, resizes and re-encodes
        except Exception:
            data = p.read_bytes()
        book.set_cover(p.name, data)

    # Simple HTML content with optional embedded CSS
    combined_css = css_text or None
    if css_file:
        css_path = Path(css_file)
        if not css_path.exists():
            raise FileNotFoundError(f"EPUB CSS file not found: {css_file}")
        css_from_file = css_path.read_text(encoding="utf-8")
        combined_css = (combined_css or "") + css_from_file

    head = (
        "<head><meta charset='utf-8'/>"
        + (f"<style>{epub.escape_html(combined_css)}</style>" if combined_css else "")
        + "</head>"
    )
    html_parts = [head, "<body>", "<h1>" + (title or "Transcript") + "</h1>"]
    for para in text.split("\n\n"):
        html_parts.append("<p>" + "<br/>".join(epub.escape_html(p) for p in para.splitlines()) + "</p>")
    html_parts.append("</body>")
    content = "\n".join(html_parts)
    c = epub.EpubHtml(title="Transcript", file_name="transcript.xhtml", lang="en")
    c.content = content
    book.add_item(c)
    book.toc = (epub.Link("transcript.xhtml", "Transcript", "transcript"),)
    book.add_item(epub.EpubNavi())
    book.add_item(epub.EpubNav())
    book.add_item(epub.EpubNCX())
    book.spine = ["nav", c]
    epub.write_epub(out_path, book)


def _export_kindle(
    text: str,
    out_path: str,
    target_fmt: str,
    title: Optional[str],
    author: Optional[str],
    cover_image: Optional[str] = None,
    css_file: Optional[str] = None,
    css_text: Optional[str] = None,
):
    conv = shutil.which("ebook-convert")
    if not conv:
        raise RuntimeError(
            "Kindle formats require Calibre's 'ebook-convert' to be installed and on PATH."
        )
    # Make a temp EPUB then convert to target
    fd, tmp_epub = tempfile.mkstemp(prefix="transcript_", suffix=".epub")
    os.close(fd)
    try:
        _export_epub(
            text,
            tmp_epub,
            title=title,
            author=author,
            cover_image=cover_image,
            css_file=css_file,
            css_text=css_text,
        )
        subprocess.run([conv, tmp_epub, out_path], check=True)
    finally:
        try:
            Path(tmp_epub).unlink(missing_ok=True)
        except Exception:
            pass


def _prepare_cover_bytes(path: Path) -> bytes:
    Image = None
    try:
        import importlib
        Image = importlib.import_module("PIL.Image")  # type: ignore
    except Exception:
        try:
            from PIL import Image as PILImage  # type: ignore
            Image = PILImage
        except Exception:
            return path.read_bytes()

    max_size = (1600, 2560)
    with Image.open(str(path)) as img:
        img = img.convert("RGB")
        img.thumbnail(max_size, Image.LANCZOS)
        import io

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        data = buf.getvalue()
        if not data:
            return path.read_bytes()
        return data
