import podcast_transcriber.cli as cli


def test_load_config_uses_tomli_fallback(tmp_path, monkeypatch):
    # Create a minimal TOML config
    cfg = tmp_path / "conf.toml"
    cfg.write_text(
        "\n".join(
            [
                "format = \"md\"",
                "url = \"X:/dummy.wav\"",
                "service = \"whisper\"",
                f"output = \"{str(tmp_path / 'o.md')}\"",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Remove tomllib and provide a fake tomli with basic loads()
    import sys

    sys.modules.pop("tomllib", None)

    class FakeTomli:
        @staticmethod
        def loads(s: str):
            data = {}
            for line in s.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"')
                    if k:
                        data[k] = v
            return data

    sys.modules["tomli"] = FakeTomli()

    d = cli._load_config(str(cfg))
    assert d.get("format") == "md"
    assert d.get("service") == "whisper"


def test_main_reads_defaults_from_config(tmp_path, monkeypatch):
    # Dummy audio and config that sets url/service/format/output
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF....")
    out = tmp_path / "x.md"
    cfg = tmp_path / "c.toml"
    cfg.write_text(
        f"format = \"md\"\nurl = \"{audio}\"\nservice = \"whisper\"\noutput = \"{out}\"\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "podcast_transcriber.utils.downloader.ensure_local_audio",
        lambda s: str(audio),
    )

    class Svc:
        def transcribe(self, *a, **kw):
            return "CFG"

    monkeypatch.setattr("podcast_transcriber.services.get_service", lambda name: Svc())

    code = cli.main(["--config", str(cfg)])
    assert code == 0
    assert out.exists() and out.read_text(encoding="utf-8").strip() == "CFG"
