from pathlib import Path

import podcast_transcriber.exporters.exporter as exp


def test_kindle_azw_maps_to_azw3(tmp_path, monkeypatch):
    # Arrange a dummy text and output path
    out_path = tmp_path / "book.azw"

    # Pretend Calibre is installed
    monkeypatch.setattr(exp.shutil, "which", lambda name: "/usr/bin/ebook-convert")

    # Avoid real EPUB creation; just stub it to write something
    monkeypatch.setattr(
        exp, "_export_epub", lambda text, out, **kw: Path(out).write_bytes(b"EPUB")
    )

    # Intercept subprocess.run to simulate successful conversion to a temp .azw3
    def fake_run(args, check):
        # args: [conv, tmp_epub, dest]
        dest = args[2]
        # Write some bytes to the destination to emulate Calibre output
        Path(dest).write_bytes(b"AZW3DATA")

    monkeypatch.setattr(exp.subprocess, "run", fake_run)

    # Act: request azw target; exporter should convert to azw3 internally and then copy to .azw
    exp._export_kindle(
        text="hello",
        out_path=str(out_path),
        target_fmt="azw",
        title="T",
        author="A",
        cover_image=None,
        css_file=None,
        css_text=None,
    )

    # Assert: final .azw path is created and contains the converted bytes
    assert out_path.exists()
    assert out_path.read_bytes() == b"AZW3DATA"
