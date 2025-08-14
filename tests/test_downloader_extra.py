from pathlib import Path
from types import SimpleNamespace

import podcast_transcriber.utils.downloader as dl


def test_rss_feed_enclosure_download(monkeypatch, tmp_path):
    # Fake RSS XML with one <enclosure url="..."> element
    audio_url = "https://example.com/test.mp3"
    rss_xml = f"""
    <rss><channel>
      <item>
        <title>Ep</title>
        <enclosure url="{audio_url}"/>
      </item>
    </channel></rss>
    """.strip()

    class FakeResp:
        def __init__(self, content=b"", headers=None, text=""):
            self._content = content
            self.headers = headers or {"content-type": "audio/mpeg"}
            self.text = text

        def iter_content(self, chunk_size=8192):
            yield self._content

        def raise_for_status(self):
            return None

    # Return RSS for the .xml URL, and audio bytes otherwise
    def fake_get(url, **kwargs):
        if url.endswith(".xml"):
            return FakeResp(text=rss_xml, headers={"content-type": "text/xml"})
        return FakeResp(content=b"DATA", headers={"content-type": "audio/mpeg"})

    monkeypatch.setattr(dl, "_require_requests", lambda: SimpleNamespace(get=fake_get))

    # Ensure ensure_local_audio can resolve enclosure and download audio
    p = dl.ensure_local_audio("https://example.com/feed.xml")
    pth = Path(p)
    assert pth.exists()
    assert pth.read_bytes() == b"DATA"
    pth.unlink()


def test_http_retry_logic(monkeypatch):
    # First two attempts fail, third succeeds
    attempts = {"n": 0}

    class Boom(Exception):
        pass

    class FakeResp:
        headers = {"content-type": "audio/mpeg"}

        def iter_content(self, chunk_size=8192):  # pragma: no cover - unused in this test
            yield b"X"

        def raise_for_status(self):
            return None

    def flaky_get(url, **kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise Boom("fail")
        return FakeResp()

    monkeypatch.setattr(dl, "_require_requests", lambda: SimpleNamespace(get=flaky_get))

    # Call the internal helper via the public path by triggering a URL download
    # (we don't actually write a file in this test; we just ensure it doesn't raise)
    resp = dl._http_get("https://example.com/a.mp3", retries=3, backoff=0.0)
    assert isinstance(resp, FakeResp)
