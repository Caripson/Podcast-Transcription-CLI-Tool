from podcast_transcriber.exporters.exporter import export_transcript


def test_export_md_formatting(tmp_path):
    out = tmp_path / "doc.md"
    text = "Para1\n\nPara2"
    export_transcript(text, str(out), "md", title="My Title", author="Alice")
    data = out.read_text(encoding="utf-8").splitlines()
    # First line is # Title; author in italic; headings or paragraphs preserved
    assert data[0] == "# My Title"
    assert "_by Alice_" in data[2]
    assert "Para1" in "\n".join(data)
    assert "Para2" in "\n".join(data)


def test_export_txt_formatting(tmp_path):
    out = tmp_path / "doc.txt"
    text = "P1\n\nP2"
    export_transcript(text, str(out), "txt", title="T", author="Bob")
    data = out.read_text(encoding="utf-8")
    # TXT format writes raw text only (no title/author header)
    assert data.splitlines()[0] == "P1"
    assert "by Bob" not in data
    assert "P1" in data and "P2" in data
