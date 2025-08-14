THEMES = {
    "minimal": (
        "body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; }\n"
        "h1 { font-size: 1.6em; margin-top: 0.2em; }\n"
        "p { margin: 0.6em 0; }\n"
        "code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }"
    ),
    "reader": (
        "body { font-family: Georgia, 'Times New Roman', serif; font-size: 1.15em; line-height: 1.65; margin: 0; }\n"
        "h1 { font-size: 1.8em; margin: 0.4em 0; }\n"
        "p { margin: 0.8em 0; text-align: justify; }"
    ),
    "classic": (
        "body { font-family: 'Times New Roman', Times, serif; font-size: 1.0em; line-height: 1.6; }\n"
        "h1 { font-size: 1.6em; margin: 0.5em 0; }\n"
        "p { margin: 0.7em 0; }"
    ),
    "dark": (
        "html, body { background: #121212; color: #e0e0e0; }\n"
        "body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; }\n"
        "h1 { color: #ffffff; border-bottom: 1px solid #333; padding-bottom: 0.2em; }\n"
        "p { margin: 0.7em 0; }\n"
        "a { color: #80cbc4; }\n"
        "code, pre { background: #1e1e1e; color: #cfcfcf; }"
    ),
}


def get_theme_css(name: str) -> str:
    return THEMES.get(name, "")


def list_themes():
    return sorted(THEMES.keys())
