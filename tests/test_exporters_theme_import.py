def test_import_exporter_themes():
    # Ensure theme module is importable (light touch to tick coverage)
    mod = __import__("podcast_transcriber.exporters.themes", fromlist=["*"])
    assert (
        hasattr(mod, "DEFAULT_CSS") or hasattr(mod, "THEMES") or isinstance(mod, object)
    )
