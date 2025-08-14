from podcast_transcriber.utils import cache as c


def test_cache_compute_get_set(tmp_path):
    # Create a local file to influence key stat
    f = tmp_path / "a.wav"
    f.write_bytes(b"RIFF..")
    key = c.compute_key("src", "svc", ("opt1", "opt2"), local_path=str(f))
    assert isinstance(key, str) and len(key) == 64
    # Write and read back
    c.set(str(tmp_path), key, {"text": "hello", "segments": []})
    got = c.get(str(tmp_path), key)
    assert got and got["text"] == "hello"
