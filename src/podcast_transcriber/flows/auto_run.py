from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime

from ..orchestrator import load_yaml_config, cmd_ingest, cmd_process, cmd_send
from ..storage.state import StateStore


log = logging.getLogger("podcast.auto_run")


def _run_once(config_path: str) -> None:
    # Ingest
    args_ing = argparse.Namespace(config=config_path, feed=None)
    cmd_ingest(args_ing)
    # Get last job
    store = StateStore()
    jobs = store.state.get("jobs", [])
    if not jobs:
        log.info("No jobs created.")
        return
    job_id = jobs[-1].get("id")
    # Process and send
    cmd_process(argparse.Namespace(job_id=job_id))
    cmd_send(argparse.Namespace(job_id=job_id))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="podcast-auto-run", description="Schedule ingest→process→send runs")
    ap.add_argument("--config", required=True, help="Path to YAML config")
    ap.add_argument("--interval", default="daily", choices=["hourly", "daily"], help="Run frequency")
    ap.add_argument("--once", action="store_true", help="Run only once and exit")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.once:
        _run_once(args.config)
        return 0

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore
    except Exception as e:
        raise SystemExit("Scheduler requires APScheduler. Install with: pip install apscheduler or podcast-transcriber[scheduler]") from e

    sched = BlockingScheduler()
    if args.interval == "hourly":
        sched.add_job(lambda: _run_once(args.config), "interval", hours=1, id="podcast-job")
    else:
        sched.add_job(lambda: _run_once(args.config), "cron", hour=3, id="podcast-job")
    log.info("Scheduler started (%s)", args.interval)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

