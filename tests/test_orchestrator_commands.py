import importlib


def test_cmd_digest_writes_epub(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))
    orch = importlib.import_module("podcast_transcriber.orchestrator")

    # Work in a temp CWD because cmd_digest writes to ./out
    monkeypatch.chdir(tmp_path)

    # Recent episodes returned by store
    monkeypatch.setattr(
        orch.StateStore,
        "list_recent",
        lambda self, days=7, feed_name=None: [
            {"title": "Ep1", "slug": "ep1", "text": "T1"},
            {"title": "Ep2", "slug": "ep2", "text": "T2"},
        ],
    )

    # Write a small EPUB placeholder
    monkeypatch.setattr(
        orch,
        "export_book",
        lambda chapters, out_path, fmt, title=None, author=None: __import__("pathlib")
        .Path(out_path)
        .write_bytes(b"EPUB"),
    )

    rc = orch.cmd_digest(type("A", (), {"feed": None, "weekly": True})())
    assert rc == 0
    # Ensure file got written to ./out
    out_dir = tmp_path / "out"
    assert out_dir.exists()
    assert any(
        p.suffix == ".epub" and p.read_bytes().startswith(b"EPUB")
        for p in out_dir.iterdir()
    )


def test_cmd_run_invokes_process_and_send(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))
    orch = importlib.import_module("podcast_transcriber.orchestrator")

    monkeypatch.setattr(orch, "load_yaml_config", lambda p: {"service": "echo"})
    # Minimal store behavior
    monkeypatch.setattr(
        orch.StateStore,
        "create_job",
        lambda self, cfg: {"id": "job-xyz", "episodes": [], "config": cfg},
    )
    called = {"proc": False, "send": False}
    monkeypatch.setattr(
        orch, "cmd_process", lambda args: called.__setitem__("proc", True) or 0
    )
    monkeypatch.setattr(
        orch, "cmd_send", lambda args: called.__setitem__("send", True) or 0
    )

    rc = orch.cmd_run(type("A", (), {"config": str(tmp_path / "cfg.yml")})())
    assert rc == 0 and called["proc"] and called["send"]
