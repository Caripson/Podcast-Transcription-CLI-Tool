import pytest

import podcast_transcriber.cli as cli


def test_cli_requires_url(tmp_path, monkeypatch):
    # With only --service, missing --url should exit with a helpful message
    with pytest.raises(SystemExit) as exc:
        cli.main(["--service", "whisper"])  # no --url
    assert "--url is required" in str(exc.value)


def test_cli_requires_service(tmp_path, monkeypatch):
    f = tmp_path / "a.wav"
    f.write_bytes(b"RIFF..")
    with pytest.raises(SystemExit) as exc:
        cli.main(["--url", str(f)])  # no --service
    assert "--service is required" in str(exc.value)

