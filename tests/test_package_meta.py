def test_import___main__():
    # Importing __main__ should not run the CLI (guarded), but should execute top-level import.
    mod = __import__("podcast_transcriber.__main__", fromlist=["*"])
    assert hasattr(mod, "main")


def test_themes_helpers():
    from podcast_transcriber.exporters import themes

    names = themes.list_themes()
    assert isinstance(names, list) and "minimal" in names
    css = themes.get_theme_css("minimal")
    assert isinstance(css, str) and "body" in css
