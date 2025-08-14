from __future__ import annotations

from typing import Dict, List, Tuple


def segment_by_simple_rules(text: str, max_chars: int = 4000) -> List[Dict[str, str]]:
    """Very simple fallback segmenter that creates topic-like chunks.

    Splits on double newlines and groups into chunks of ~max_chars.
    Returns a list of {title, text}.
    """
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: List[Dict[str, str]] = []
    buf: List[str] = []
    size = 0
    for p in paras:
        buf.append(p)
        size += len(p)
        if size >= max_chars:
            out.append({"title": f"Ämne {len(out)+1}", "text": "\n\n".join(buf)})
            buf, size = [], 0
    if buf:
        out.append({"title": f"Topic {len(out)+1}", "text": "\n\n".join(buf)})
    return out


def segment_with_embeddings(text: str, threshold: float = 0.75, max_chunk_chars: int = 6000) -> List[Dict[str, str]]:
    """Optional semantic segmentation using sentence embeddings.

    Requires 'sentence-transformers'. Falls back to simple rules if unavailable.
    Groups sentences into topical chunks where similarity dips below threshold.
    """
    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore
    except Exception:
        return segment_by_simple_rules(text, max_chars=max_chunk_chars)
    import re
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    sents = [s for s in sents if s]
    if not sents:
        return [{"title": "Topic 1", "text": text.strip()}]
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embs = model.encode(sents, convert_to_tensor=True, show_progress_bar=False)
    chunks: List[Dict[str, str]] = []
    buf: List[str] = [sents[0]]
    last_idx = 0
    for i in range(1, len(sents)):
        sim = float(util.cos_sim(embs[i - 1], embs[i]).item())
        if sim < threshold or sum(len(x) for x in buf) > max_chunk_chars:
            chunks.append({"title": f"Topic {len(chunks)+1}", "text": " ".join(buf)})
            buf = []
        buf.append(sents[i])
    if buf:
        chunks.append({"title": f"Topic {len(chunks)+1}", "text": " ".join(buf)})
    return chunks


def key_takeaways(text: str, max_points: int = 5) -> List[str]:
    """Very simple key takeaway extraction by frequent noun-ish phrases.

    Placeholder for a more robust summarizer. Keeps logic lightweight.
    """
    import re
    words = re.findall(r"[A-Za-zÅÄÖåäö0-9']+", text)
    freq = {}
    for w in words:
        if len(w) < 4:
            continue
        w2 = w.lower()
        freq[w2] = freq.get(w2, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [w for w, _ in ranked[:max_points]]


def key_takeaways_better(text: str, max_points: int = 5) -> List[str]:
    """Improved key takeaways extractor.

    Strategy:
    - If spaCy is available, use noun chunks and most frequent lemma nouns.
    - Otherwise, fall back to a lightweight noun-ish phrase regex and frequency ranking.
    """
    # Try spaCy first
    try:
        import spacy  # type: ignore
        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            # Fallback to a multilingual small model if available
            try:
                nlp = spacy.blank("en")  # minimal tokenizer; no POS tags
            except Exception:
                nlp = None
        if nlp is not None and hasattr(nlp, "pipe") and getattr(nlp, "has_pipe", lambda *a, **k: False)("tagger"):
            doc = nlp(text)
            phrases = [chunk.text.strip() for chunk in getattr(doc, "noun_chunks", []) if chunk.text.strip()]
            # fallback if no noun_chunks
            if not phrases:
                phrases = [t.lemma_ for t in doc if t.is_alpha and t.pos_ in {"NOUN", "PROPN"}]
            freq: Dict[str, int] = {}
            for p in phrases:
                key = p.lower()
                freq[key] = freq.get(key, 0) + 1
            ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
            return [p for p, _ in ranked[:max_points]]
    except Exception:
        pass

    # Regex-based simple noun-ish phrase extraction
    import re
    # Capture Capitalized phrases and mid-length lowercase multi-words as candidates
    caps = re.findall(r"(?:[A-Z][a-z]+(?: [A-Z][a-z]+){0,3})", text)
    words = re.findall(r"[A-Za-zÅÄÖåäö0-9']+", text)
    # Build frequency with preference for multiword caps
    freq: Dict[str, int] = {}
    for p in caps:
        k = p.strip().lower()
        if len(k) >= 4:
            freq[k] = freq.get(k, 0) + 3  # boost phrases
    for w in words:
        if len(w) < 4:
            continue
        k = w.lower()
        freq[k] = freq.get(k, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [p for p, _ in ranked[:max_points]]
