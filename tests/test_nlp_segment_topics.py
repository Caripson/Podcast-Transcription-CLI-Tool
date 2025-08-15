import sys

from podcast_transcriber.nlp import segment_topics as st


def test_segment_by_simple_rules_chunks_by_size():
    text = "Para1" + "\n\n" + "Para2" + "\n\n" + ("x" * 10)
    chunks = st.segment_by_simple_rules(text, max_chars=5)
    assert isinstance(chunks, list) and chunks
    # Should produce multiple chunks due to low max_chars
    assert len(chunks) >= 2
    assert all("text" in c and c["text"] for c in chunks)


def test_segment_with_embeddings_fallback_when_library_missing():
    # Ensure sentence_transformers import fails to trigger fallback
    sys.modules.pop("sentence_transformers", None)
    text = "Sentence one. Sentence two."
    chunks = st.segment_with_embeddings(text, threshold=0.99, max_chunk_chars=10)
    assert isinstance(chunks, list) and chunks


def test_key_takeaways_simple():
    text = "OpenAI builds useful tools for developers. Developers love useful tools."
    kws = st.key_takeaways(text, max_points=3)
    assert isinstance(kws, list) and kws
    # Expect words like 'developers' or 'tools' to appear
    assert any(k in kws for k in ("developers", "tools"))


def test_key_takeaways_better_regex_fallback(monkeypatch):
    class FakeNLP:
        def __init__(self):
            self._pipes = set()

        def has_pipe(self, name):
            return False

        @property
        def pipe(self):  # attribute to satisfy hasattr(nlp, "pipe")
            return True

    class FakeSpacy:
        @staticmethod
        def load(name):
            raise RuntimeError("no model")

        @staticmethod
        def blank(lang):
            return FakeNLP()

    sys.modules["spacy"] = FakeSpacy()
    text = "OpenAI Research and Chat Completions improve Developer Experience."
    kws = st.key_takeaways_better(text, max_points=5)
    assert isinstance(kws, list) and kws
    # Should contain lowercased phrases/words extracted via regex fallback
    assert any("openai" in k or "developer" in k for k in kws)

