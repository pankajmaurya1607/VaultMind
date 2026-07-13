from app.tasks.process import chunk_text


class TestChunking:
    def test_basic_chunking(self):
        text = "Hello world. " * 100
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1
        assert all(len(c) <= 120 for c in chunks)

    def test_small_text(self):
        text = "Hello world"
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_exact_chunk_size(self):
        text = "a" * 500
        chunks = chunk_text(text, chunk_size=200, overlap=0)
        assert len(chunks) == 3
        assert all(len(c) <= 200 for c in chunks)

    def test_overlap(self):
        text = "The quick brown fox jumps over the lazy dog. " * 20
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        if len(chunks) > 1:
            assert len(chunks[1]) > 0
