import re


def normalize_text(text: str) -> str:
    # Collapse multiple spaces and lines, ensure space after punctuation
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def summarize_text(text: str, max_sentences: int = 5) -> str:
    # Naive: take first N sentences.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:max_sentences]).strip()
