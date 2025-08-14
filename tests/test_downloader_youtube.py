import json
from types import SimpleNamespace

import podcast_transcriber.utils.downloader as dl


def test_youtube_download_sets_metadata_and_writes_file(monkeypatch, tmp_path):
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Pretend yt-dlp is available
    monkeypatch.setattr(
        "shutil.which", lambda name: "/usr/bin/yt-dlp" if name == "yt-dlp" else None
    )

    # Return video metadata
    meta = {
        "title": "Cool Video",
        "thumbnail": "https://img/cover.jpg",
        "uploader": "ChannelX",
    }
    monkeypatch.setattr(
        "subprocess.check_output", lambda args: json.dumps(meta).encode("utf-8")
    )

    # When yt-dlp runs, write a tiny file to the requested output path (arg after -o)
    def fake_run(args, check=False, **kwargs):
        # find the output path following "-o"
        out_idx = args.index("-o") + 1
        out_path = args[out_idx]
        from pathlib import Path

        Path(out_path).write_bytes(b"DATA")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    p = dl.ensure_local_audio(url)
    # ensure path exists and metadata propagated on LocalAudioPath
    from pathlib import Path

    assert Path(p).exists()
    assert getattr(p, "source_title", None) == "Cool Video"
    assert getattr(p, "cover_url", None) == "https://img/cover.jpg"
    assert getattr(p, "source_uploader", None) == "ChannelX"
