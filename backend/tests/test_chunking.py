import os
import tempfile
from app.tasks.process import chunk_text, parse_file


def test_chunk_text_basic():
    text = "Word " * 500  # 2500 characters
    chunks = chunk_text(text, chunk_size=500, overlap=100)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 550  # Allows boundary padding


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text(None) == []


def test_chunk_text_short():
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=1000, overlap=200)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_parse_file_txt_and_md():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Hello from text file")
        txt_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(b"# Title\n\nMarkdown content")
        md_path = f.name

    try:
        assert parse_file(txt_path, "text/plain") == "Hello from text file"
        assert "# Title" in parse_file(md_path, "text/markdown")
    finally:
        if os.path.exists(txt_path):
            os.remove(txt_path)
        if os.path.exists(md_path):
            os.remove(md_path)
