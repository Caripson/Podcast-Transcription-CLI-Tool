from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

STATE_DIR = Path(
    os.environ.get(
        "PODCAST_STATE_DIR", str(Path.home() / ".local/state/podcast_transcriber")
    )
)
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = STATE_DIR / "state.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class StateStore:
    def __init__(self):
        self._load()

    def _load(self):
        if STATE_PATH.exists():
            try:
                self.state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            except Exception:
                self.state = {"jobs": [], "episodes": [], "seen": {}}
        else:
            self.state = {"jobs": [], "episodes": [], "seen": {}}

    def _save(self):
        STATE_PATH.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def create_job(self, config: dict[str, Any], feed_name: str | None = None) -> dict:
        job_id = f"job-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        # Placeholder episodes; proper feed fetch should populate these
        episodes = []  # populated by orchestrator.ingest using ingestion.feed
        job = {
            "id": job_id,
            "created_at": _now_iso(),
            "status": "new",
            "episodes": episodes,
            "config": config,
        }
        self.state.setdefault("jobs", []).append(job)
        self._save()
        return job

    def create_job_with_episodes(
        self, config: dict[str, Any], episodes: list[dict]
    ) -> dict:
        job = self.create_job(config)
        job["episodes"] = episodes
        self.save_job(job)
        return job

    def get_job(self, job_id: str) -> dict | None:
        for j in self.state.get("jobs", []):
            if j.get("id") == job_id:
                return j
        return None

    def save_job(self, job: dict) -> None:
        jobs = self.state.get("jobs", [])
        for i, j in enumerate(jobs):
            if j.get("id") == job.get("id"):
                jobs[i] = job
                break
        else:
            jobs.append(job)
        self._save()

    def list_recent(self, days: int = 7, feed_name: str | None = None) -> list[dict]:
        # naive: collect episodes from recent jobs
        cutoff = datetime.utcnow() - timedelta(days=days)
        out = []
        for j in self.state.get("jobs", []):
            try:
                dt = datetime.fromisoformat(j.get("created_at", "").rstrip("Z"))
            except Exception:
                continue
            if dt < cutoff:
                continue
            for ep in j.get("episodes", []):
                if feed_name and ep.get("feed") != feed_name:
                    continue
                out.append(ep)
        return out

    # Duplicate detection helpers
    def has_seen(self, feed: str, key: str | None) -> bool:
        if not key:
            return False
        seen = self.state.setdefault("seen", {})
        keys = set(seen.setdefault(feed, []))
        return key in keys

    def mark_seen(self, feed: str, key: str | None) -> None:
        if not key:
            return
        seen = self.state.setdefault("seen", {})
        arr = list(seen.setdefault(feed, []))
        if key not in arr:
            arr.append(key)
            seen[feed] = arr
            self._save()
