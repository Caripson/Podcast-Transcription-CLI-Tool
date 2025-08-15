from podcast_transcriber.utils.downloader import (
    _guess_extension_from_headers,
    is_url,
    ensure_local_audio,
    LocalAudioPath,
)


def test_guess_extension_from_headers_variants():
    assert _guess_extension_from_headers({"content-type": "audio/mpeg"}) == ".mp3"
    assert _guess_extension_from_headers({"content-type": "audio/x-m4a"}) == ".m4a"
    assert _guess_extension_from_headers({"content-type": "audio/wav"}) == ".wav"
    assert _guess_extension_from_headers({"content-type": "audio/ogg"}) == ".ogg"
    assert _guess_extension_from_headers({"content-type": "text/plain"}) == ""


def test_is_url_and_ensure_local(tmp_path):
    assert is_url("http://example.com/a.mp3")
    p = tmp_path / "a.wav"
    p.write_bytes(b"RIFF..")
    lp = ensure_local_audio(str(p))
    # returns LocalAudioPath-like
    assert isinstance(lp, LocalAudioPath)
    assert str(lp).endswith("a.wav") and not bool(getattr(lp, "is_temp", False))
