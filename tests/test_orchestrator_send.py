from pathlib import Path


def test_cmd_send_emails_artifacts(monkeypatch, tmp_path):
    # Isolate state and output
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))

    # Prepare a job with a fake artifact
    from podcast_transcriber.storage.state import StateStore

    store = StateStore()
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / "episode.epub"
    artifact_path.write_bytes(b"EPUB")

    job = store.create_job(
        {
            "service": "echo",
            "output_dir": str(out_dir),
            "kindle": {},
            "smtp": {},
        }
    )
    job["artifacts"] = [{"output": str(artifact_path)}]
    store.save_job(job)

    # SMTP and Kindle settings via env
    monkeypatch.setenv("KINDLE_TO_EMAIL", "to@example.com")
    monkeypatch.setenv("KINDLE_FROM_EMAIL", "from@example.com")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASS", "pass")

    calls = []

    def fake_send(**kwargs):
        calls.append(kwargs)

    # Patch low-level sender
    monkeypatch.setattr(
        "podcast_transcriber.orchestrator.send_file_via_smtp",
        fake_send,
    )

    from podcast_transcriber.orchestrator import cmd_send

    rc = cmd_send(type("A", (), {"job_id": job["id"]})())
    assert rc == 0
    assert calls and Path(calls[0]["attachment_path"]).name == "episode.epub"
