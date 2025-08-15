def test_discover_categories_and_image(monkeypatch):
    from types import SimpleNamespace
    from podcast_transcriber.ingestion import feed as ing

    # Fake parsed feed with entries carrying tags, description, and itunes image
    entry = SimpleNamespace(
        id="id1",
        title="T",
        link="https://ex/1",
        enclosures=[{"href": "https://ex/1.mp3"}],
        tags=[SimpleNamespace(term="Creative Commons")],
        summary="Desc",
        itunes_image={"href": "https://ex/cover.jpg"},
    )
    parsed = SimpleNamespace(feed=SimpleNamespace(tags=[SimpleNamespace(term="Creative Commons")]), entries=[entry])

    def fake_load(url):
        return parsed

    monkeypatch.setattr(ing, "_load_feed", fake_load)

    class DummyStore:
        def __init__(self):
            self.seen = set()

        def has_seen(self, feed, key):
            return False

        def mark_seen(self, feed, key):
            self.seen.add((feed, key))

    cfg = {
        "feeds": [
            {
                "name": "F",
                "url": "https://ex/rss.xml",
                "categories": ["creative commons"],
            }
        ]
    }
    eps = ing.discover_new_episodes(cfg, DummyStore())
    assert len(eps) == 1
    ep = eps[0]
    assert ep.get("image")
    assert "creative commons" in [c.lower() for c in ep.get("categories", [])]
    assert ep.get("description") == "Desc"

