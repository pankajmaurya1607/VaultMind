import pytest
from unittest.mock import patch, MagicMock, mock_open
from app.tasks.process import parse_file, chunk_text


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
    text = "one two three four five six seven eight nine ten"
    chunks = chunk_text(text, chunk_size=5, overlap=2)
    assert len(chunks) >= 2
    if len(chunks) >= 2:
        first_words = chunks[0].split()
        second_words = chunks[1].split()
        overlap_words = set(first_words) & set(second_words)
        assert len(overlap_words) > 0
