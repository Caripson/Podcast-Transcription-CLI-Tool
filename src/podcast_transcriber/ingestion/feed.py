from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _load_feed(url: str):
    try:
        import feedparser  # type: ignore
    except Exception as e:
        raise RuntimeError("Feed ingestion requires 'feedparser'. Install with: pip install feedparser or pip install podcast-transcriber[ingest]") from e
    return feedparser.parse(url)


def _try_podcastindex(url: str):
    """Optional: query PodcastIndex for episodes by feed URL when API creds are available.

    Requires PODCASTINDEX_API_KEY and PODCASTINDEX_API_SECRET environment variables.
    """
    import os
    key = os.environ.get("PODCASTINDEX_API_KEY")
    secret = os.environ.get("PODCASTINDEX_API_SECRET")
    if not key or not secret:
        return None
    try:
        import requests  # type: ignore
    except Exception:
        return None
    ts = int(time.time())
    data = f"{key}{ts}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), data, hashlib.sha1).hexdigest()
    headers = {
        "User-Agent": "podcast-transcriber/1",
        "X-Auth-Date": str(ts),
        "X-Auth-Key": key,
        "Authorization": sig,
        "Content-Type": "application/json",
    }
    try:
        r = requests.get(
            "https://podcastindex.org/api/1.0/episodes/byfeedurl",
            params={"url": url, "max": 20},
            headers=headers,
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _podcastindex_request(endpoint: str, params: dict):
    """Low-level PodcastIndex request helper with auth headers.

    Returns parsed JSON or None on failure.
    """
    import os
    key = os.environ.get("PODCASTINDEX_API_KEY")
    secret = os.environ.get("PODCASTINDEX_API_SECRET")
    if not key or not secret:
        return None
    try:
        import requests  # type: ignore
    except Exception:
        return None
    ts = int(time.time())
    data = f"{key}{ts}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), data, hashlib.sha1).hexdigest()
    headers = {
        "User-Agent": "podcast-transcriber/1",
        "X-Auth-Date": str(ts),
        "X-Auth-Key": key,
        "Authorization": sig,
        "Content-Type": "application/json",
    }
    try:
        r = requests.get(
            f"https://podcastindex.org/api/1.0/{endpoint}",
            params=params,
            headers=headers,
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


from typing import Optional


def _podcastindex_by_id(feedid: Optional[str] = None, guid: Optional[str] = None):
    if feedid:
        return _podcastindex_request("episodes/byfeedid", {"id": feedid, "max": 20})
    if guid:
        return _podcastindex_request("episodes/bypodcastguid", {"guid": guid, "max": 20})
    return None


def discover_new_episodes(config: dict, store) -> List[Dict[str, Any]]:
    """Discover new episodes from configured feeds using feedparser.

    Avoids duplicates via store.has_seen(feed, id/link). Returns list of episode dicts.
    """
    feeds = config.get("feeds") or []
    episodes: List[Dict[str, Any]] = []
    for f in feeds:
        name = f.get("name") or f.get("url") or f.get("podcastindex_feedid") or f.get("podcast_guid") or "feed"
        url = f.get("url")
        pi = None
        # Try PodcastIndex by feed ID or GUID first
        feedid = f.get("podcastindex_feedid")
        pguid = f.get("podcast_guid")
        if feedid or pguid:
            pi = _podcastindex_by_id(feedid=feedid, guid=pguid)
        elif url:
            # Prefer PodcastIndex when API creds present; fall back to feedparser
            pi = _try_podcastindex(url)
        entries = []
        if pi and isinstance(pi, dict) and pi.get("items"):
            for it in pi.get("items", []):
                entries.append({
                    "id": it.get("id") or it.get("guid"),
                    "title": it.get("title"),
                    "link": it.get("link"),
                    "enclosureUrl": it.get("enclosureUrl") or it.get("enclosure_url"),
                })
        else:
            if not url:
                continue
            parsed = _load_feed(url)
            for entry in parsed.entries or []:
                entries.append(entry)
        for entry in entries:
            guid = getattr(entry, "id", None) or getattr(entry, "guid", None) or getattr(entry, "link", None)
            link = getattr(entry, "link", None)
            if not link and isinstance(entry, dict):
                link = entry.get("link")
            if store.has_seen(name, guid or link):
                continue
            title = (getattr(entry, "title", None) if not isinstance(entry, dict) else entry.get("title")) or "Episode"
            media_url = None
            # try common enclosure
            try:
                if isinstance(entry, dict):
                    media_url = entry.get("enclosureUrl") or entry.get("enclosure_url")
                else:
                    enclosures = getattr(entry, "enclosures", [])
                    if enclosures:
                        media_url = enclosures[0].get("href")
            except Exception:
                pass
            if not media_url:
                # sometimes in links
                media_url = link
            if not media_url:
                continue
            ep = {
                "feed": name,
                "title": title,
                "slug": (title.lower().replace(" ", "-")[:40] if title else f"{name}-ep"),
                "source": media_url,
                "guid": guid or link,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            episodes.append(ep)
            store.mark_seen(name, guid or link)
    return episodes
