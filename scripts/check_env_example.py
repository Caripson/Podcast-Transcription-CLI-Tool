#!/usr/bin/env python3
import sys
from pathlib import Path

REQUIRED_KEYS = [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASS",
    "KINDLE_TO_EMAIL",
    "KINDLE_FROM_EMAIL",
    "PODCASTINDEX_API_KEY",
    "PODCASTINDEX_API_SECRET",
]

def parse_env(path: Path):
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data

def main():
    p = Path(".env.example")
    if not p.exists():
        print(".env.example not found", file=sys.stderr)
        return 2
    env = parse_env(p)
    missing = [k for k in REQUIRED_KEYS if k not in env]
    if missing:
        print(f"Missing required keys in .env.example: {', '.join(missing)}", file=sys.stderr)
        return 3
    # Basic sanity: ensure no obvious secrets committed (heuristic)
    bad = []
    for k, v in env.items():
        if k.endswith("PASS") or k.endswith("SECRET") or k.endswith("KEY"):
            if v and len(v) > 5 and "example" not in v.lower():
                bad.append(k)
    if bad:
        print(f"Suspicious non-empty secret-like values in .env.example: {', '.join(bad)}", file=sys.stderr)
        return 4
    print(".env.example looks OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

