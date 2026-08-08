from unittest.mock import mock_open, patch

from app.tasks.process import chunk_text, parse_file


def test_parse_txt():
    content = b"Hello world\nThis is a test file."
    mock_file = mock_open(read_data=content)
    with patch("builtins.open", mock_file):
        result = parse_file("/fake/path/test.txt", "text/plain")
    assert result == "Hello world\nThis is a test file."


def test_parse_unsupported_format():
    result = parse_file("/fake/path/test.xyz", "application/octet-stream")
    assert result == ""


def test_chunk_text_basic():
    text = "word " * 50
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 25 for c in chunks)


def test_chunk_text_small():
    text = "short text"
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == "short text"


def test_chunk_text_overlap():
    text = (
        "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua. "
    ) * 4
    chunks = chunk_text(text, chunk_size=50, overlap=20)
    assert len(chunks) >= 2
    for prev, curr in zip(chunks, chunks[1:]):
        shared = set(prev.split()) & set(curr.split())
        assert len(shared) > 0
