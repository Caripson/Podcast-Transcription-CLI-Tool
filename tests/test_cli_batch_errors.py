import pytest

import podcast_transcriber.cli as cli


def test_cli_batch_requires_output_dir_when_not_combining(tmp_path, monkeypatch):
    # Create list file
    lst = tmp_path / "list.txt"
    lst.write_text("/tmp/a.wav\n", encoding="utf-8")
    # Provide required url to satisfy top-level validation; batch branch checks output
    # Avoid filesystem dependency for --url
    monkeypatch.setattr(
        "podcast_transcriber.cli.ensure_local_audio",
        lambda s: str(tmp_path / "placeholder.wav"),
    )
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "--service",
                "whisper",
                "--url",
                str(tmp_path / "placeholder.wav"),
                "--input-file",
                str(lst),
                # no --output dir and no --combine-into
            ]
        )
    assert "--output directory is required for --input-file" in str(exc.value)
