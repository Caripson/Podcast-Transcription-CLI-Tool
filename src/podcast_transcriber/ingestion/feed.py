from __future__ import annotations

import hashlib
import hmac
import time
import re
from datetime import datetime, timezone
from typing import Any, Optional


def _load_feed(url: str):
    try:
        import feedparser  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Feed ingestion requires 'feedparser'. Install with: pip install feedparser or pip install podcast-transcriber[ingest]"
        ) from e
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
    data = f"{key}{ts}".encode()
    sig = hmac.new(secret.encode(), data, hashlib.sha1).hexdigest()
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
    data = f"{key}{ts}".encode()
    sig = hmac.new(secret.encode(), data, hashlib.sha1).hexdigest()
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


def _podcastindex_by_id(feedid: Optional[str] = None, guid: Optional[str] = None):
    if feedid:
        return _podcastindex_request("episodes/byfeedid", {"id": feedid, "max": 20})
    if guid:
        return _podcastindex_request(
            "episodes/bypodcastguid", {"guid": guid, "max": 20}
        )
    return None


def _sanitize_slug(name: str) -> str:
    s = (name or "").lower()
    s = s.replace(" ", "-")
    s = re.sub(r'[<>:"/\\|?\r\n*]+', "-", s)
    s = re.sub(r"\s+", "-", s)
    s = s.strip(" .-_")
    return s or "item"


def _lower_list(vals: list[str | None]) -> list[str]:
    return [str(v).strip().lower() for v in vals if v]


def _entry_categories(entry, feed_categories: list[str] | None = None) -> list[str]:
    cats: list[str] = []
    try:
        tags = getattr(entry, "tags", None)
        if tags:
            for t in tags:
                term = getattr(t, "term", None) or getattr(t, "label", None)
                if term:
                    cats.append(str(term))
    except Exception:
        pass
    if isinstance(entry, dict):
        for k in ("categories", "category"):
            v = entry.get(k)
            if isinstance(v, (list, tuple)):
                cats.extend(map(str, v))
            elif v:
                cats.append(str(v))
    if feed_categories:
        cats.extend(feed_categories)
    return _lower_list(cats)


def _entry_image(entry, parsed=None) -> Optional[str]:
    # Try entry-level iTunes image variants
    try:
        img = getattr(entry, "image", None)
        if isinstance(img, dict):
            href = img.get("href") or img.get("url")
            if href:
                return str(href)
        elif isinstance(img, str) and img:
            return img
        ii = getattr(entry, "itunes_image", None)
        if isinstance(ii, dict):
            href = ii.get("href") or ii.get("url")
            if href:
                return str(href)
        href = getattr(entry, "itunes_image_href", None)
        if href:
            return str(href)
    except Exception:
        pass
    # Fallback to feed-level
    try:
        if parsed is not None:
            fimg = getattr(parsed.feed, "image", None)
            if isinstance(fimg, dict):
                href = fimg.get("href") or fimg.get("url")
                if href:
                    return str(href)
            href = getattr(parsed.feed, "itunes_image", None)
            if isinstance(href, dict):
                v = href.get("href") or href.get("url")
                if v:
                    return str(v)
            href2 = getattr(parsed.feed, "image_href", None)
            if href2:
                return str(href2)
    except Exception:
        pass
    return None


def _entry_description(entry, parsed=None) -> Optional[str]:
    for attr in ("summary", "description", "subtitle"):
        try:
            v = getattr(entry, attr, None)
            if v:
                return str(v)
        except Exception:
            pass
        if isinstance(entry, dict) and entry.get(attr):
            return str(entry.get(attr))
    # Fallback: feed-level description
    try:
        if parsed is not None:
            for attr in ("subtitle", "description", "summary"):
                v = getattr(parsed.feed, attr, None)
                if v:
                    return str(v)
    except Exception:
        pass
    return None


def discover_new_episodes(config: dict, store) -> list[dict[str, Any]]:
    """Discover new episodes from configured feeds using feedparser.

    Avoids duplicates via store.has_seen(feed, id/link). Returns list of episode dicts.
    """
    feeds = config.get("feeds") or []
    episodes: list[dict[str, Any]] = []
    for f in feeds:
        name = (
            f.get("name")
            or f.get("url")
            or f.get("podcastindex_feedid")
            or f.get("podcast_guid")
            or "feed"
        )
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
        categories_filter = _lower_list(
            f.get("categories", [])
            if isinstance(f.get("categories"), (list, tuple))
            else [f.get("categories")]
        )
        feed_categories: list[str] = []
        if pi and isinstance(pi, dict) and pi.get("items"):
            for it in pi.get("items", []):
                entries.append(
                    {
                        "id": it.get("id") or it.get("guid"),
                        "title": it.get("title"),
                        "link": it.get("link"),
                        "enclosureUrl": it.get("enclosureUrl")
                        or it.get("enclosure_url"),
                        "categories": list(it.get("categories", {}).values())
                        if isinstance(it.get("categories"), dict)
                        else it.get("categories"),
                        "image": (
                            it.get("image") or it.get("imageUrl") or it.get("image_url")
                        ),
                        "description": it.get("description"),
                    }
                )
        else:
            if not url:
                continue
            parsed = _load_feed(url)
            # Feed-level categories (e.g., <category>...)
            try:
                tags = getattr(parsed.feed, "tags", None)
                if tags:
                    for t in tags:
                        term = getattr(t, "term", None) or getattr(t, "label", None)
                        if term:
                            feed_categories.append(str(term))
                else:
                    c = getattr(parsed.feed, "category", None)
                    if c:
                        feed_categories.append(str(c))
            except Exception:
                pass
            for entry in parsed.entries or []:
                entries.append(entry)
        for entry in entries:
            guid = (
                getattr(entry, "id", None)
                or getattr(entry, "guid", None)
                or getattr(entry, "link", None)
            )
            link = getattr(entry, "link", None)
            if not link and isinstance(entry, dict):
                link = entry.get("link")
            if store.has_seen(name, guid or link):
                continue
            title = (
                getattr(entry, "title", None)
                if not isinstance(entry, dict)
                else entry.get("title")
            ) or "Episode"
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
            # Category filtering if requested
            if categories_filter:
                cats = _entry_categories(entry, feed_categories)
                if not any(c in cats for c in categories_filter):
                    continue
            image_url = _entry_image(entry, parsed if "parsed" in locals() else None)
            desc = _entry_description(entry, parsed if "parsed" in locals() else None)
            ep = {
                "feed": name,
                "title": title,
                "slug": _sanitize_slug(title)[:60]
                if title
                else _sanitize_slug(f"{name}-ep"),
                "source": media_url,
                "guid": guid or link,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "image": image_url,
                "description": desc,
                "categories": _entry_categories(entry, feed_categories),
            }
            episodes.append(ep)
            store.mark_seen(name, guid or link)
    return episodes
