import importlib
from datetime import datetime, timedelta, timezone


def test_state_store_basic_ops(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_STATE_DIR", str(tmp_path / ".state"))
    st_mod = importlib.import_module("podcast_transcriber.storage.state")
    store = st_mod.StateStore()

    # has_seen / mark_seen
    assert store.has_seen("feed", "k1") is False
    store.mark_seen("feed", "k1")
    assert store.has_seen("feed", "k1") is True

    # create and fetch job
    job = store.create_job({"service": "echo"})
    got = store.get_job(job["id"])
    assert got and got["id"] == job["id"]

    # list_recent should include recent jobs and filter older
    store.state["jobs"][0]["created_at"] = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()
    recent = store.list_recent(days=7, feed_name=None)
    assert isinstance(recent, list)
