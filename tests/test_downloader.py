from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from podcast_transcriber.utils.downloader import ensure_local_audio, is_url


def test_is_url_variants():
    assert is_url("https://example.com/a.mp3")
    assert is_url("http://example.com/a.wav")
    assert not is_url("file://local")
    assert not is_url("/tmp/a.wav")


def test_downloads_url_to_tempfile(monkeypatch, tmp_path):
    chunks = [b"abc", b"def", b"ghi"]

    class FakeResp:
        status_code = 200
        headers = {"content-type": "audio/mpeg"}

        def iter_content(self, chunk_size=8192):
            yield from chunks

        def raise_for_status(self):
            return None

    with mock.patch("requests.get", return_value=FakeResp()):
        p = ensure_local_audio("https://example.com/file.mp3")
        assert Path(p).exists()
        data = Path(p).read_bytes()
        assert data == b"".join(chunks)
        # cleanup
        Path(p).unlink()


def test_raises_if_local_missing(tmp_path):
    missing = tmp_path / "nope.wav"
    try:
        ensure_local_audio(str(missing))
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")

