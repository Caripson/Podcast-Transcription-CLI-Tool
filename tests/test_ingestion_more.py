from types import SimpleNamespace

from podcast_transcriber.ingestion import feed as ing


def test_sanitize_slug_and_entry_categories_dict():
    assert ing._sanitize_slug(" Hello/World? ") == "hello-world"
    entry = {"categories": ["Tech", "AI"]}
    cats = ing._entry_categories(entry)
    assert "tech" in cats and "ai" in cats


def test_discover_new_episodes_podcastindex_items(monkeypatch):
    # Force PodcastIndex path with two items
    pi = {
        "items": [
            {
                "id": "1",
                "title": "Ep1",
                "link": "https://ex/ep1",
                "enclosureUrl": "https://ex/ep1.mp3",
                "categories": {"0": "Tech"},
                "image": "https://ex/c.jpg",
                "description": "D1",
            }
        ]
    }
    monkeypatch.setattr(
        ing, "_podcastindex_by_id", lambda **kw: pi
    )

    class Store:
        def __init__(self):
            self.seen = set()

        def has_seen(self, feed, key):
            return False

        def mark_seen(self, feed, key):
            self.seen.add((feed, key))

    cfg = {"feeds": [{"name": "F", "podcastindex_feedid": "123"}]}
    eps = ing.discover_new_episodes(cfg, Store())
    assert len(eps) == 1 and eps[0]["title"] == "Ep1"


def test_discover_new_episodes_feedparser_fallback(monkeypatch):
    entry = SimpleNamespace(
        id="id1",
        title="T",
        link="https://ex/1",
        enclosures=[{"href": "https://ex/1.mp3"}],
        tags=[SimpleNamespace(term="Science")],
        summary="Desc",
        itunes_image={"href": "https://ex/cover.jpg"},
    )
    parsed = SimpleNamespace(
        feed=SimpleNamespace(tags=[SimpleNamespace(term="Science")]),
        entries=[entry],
    )
    monkeypatch.setattr(ing, "_try_podcastindex", lambda url: None)
    monkeypatch.setattr(ing, "_load_feed", lambda url: parsed)

    class Store:
        def has_seen(self, feed, key):
            return False

        def mark_seen(self, feed, key):
            pass

    cfg = {"feeds": [{"name": "F", "url": "https://ex/rss.xml"}]}
    eps = ing.discover_new_episodes(cfg, Store())
    assert len(eps) == 1 and eps[0]["image"].endswith("cover.jpg")
