from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Avoid side effects at import time. Compute preferred dirs lazily and
# create them only when we actually need to write.

APP_DIR_NAME = "podcast_transcriber"
ENV_STATE_DIR = "PODCAST_STATE_DIR"


def _preferred_state_dir() -> Path:
    env = os.environ.get(ENV_STATE_DIR)
    if env:
        return Path(env)
    xdg = os.environ.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg) / APP_DIR_NAME
    return Path.home() / ".local/state" / APP_DIR_NAME


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StateStore:
    def __init__(self):
        # Start with preferred location, but don't create directories yet.
        self._state_dir = _preferred_state_dir()
        self._state_path = self._state_dir / "state.json"
        self._load()

    def _ensure_dir(self) -> None:
        try:
            self._state_dir.mkdir(parents=True, exist_ok=True)
            return
        except Exception:
            # Fall back to a workspace-local directory to work in restricted envs/CI
            fallback = Path.cwd() / ".state" / APP_DIR_NAME
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                self._state_dir = fallback
                self._state_path = self._state_dir / "state.json"
                return
            except Exception:
                # Last resort: use current directory without subfolder
                self._state_dir = Path.cwd()
                self._state_path = self._state_dir / "state.json"

    def _load(self):
        p = self._state_path
        if p.exists():
            try:
                self.state = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                self.state = {"jobs": [], "episodes": [], "seen": {}}
        else:
            self.state = {"jobs": [], "episodes": [], "seen": {}}

    def _save(self):
        self._ensure_dir()
        self._state_path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def create_job(self, config: dict[str, Any], feed_name: str | None = None) -> dict:
        job_id = f"job-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
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
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        out = []
        for j in self.state.get("jobs", []):
            try:
                dt = datetime.fromisoformat(j.get("created_at", "").rstrip("Z"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
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
