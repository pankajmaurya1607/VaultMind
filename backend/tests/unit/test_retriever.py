from app.rag.retriever.retriever import Retriever, _rows_to_results


class TestRetrieverLocalSearch:
    def setup_method(self):
        self.retriever = Retriever()
        self.retriever._local_store = {
            1: [
                {
                    "chunk_index": 0,
                    "text": "WFH policy allows two days",
                    "metadata": {"department_id": 2},
                    "embedding": [1.0, 0.0],
                    "filename": "policy.txt",
                    "department_id": 2,
                },
                {
                    "chunk_index": 1,
                    "text": "HR contact info",
                    "metadata": {"department_id": 3},
                    "embedding": [0.0, 1.0],
                    "filename": "hr.txt",
                    "department_id": 3,
                },
            ]
        }

    def _search(self, query_vec, department_ids, top_k=5):
        return self.retriever._local_search(query_vec, department_ids, top_k)

    def test_department_filtering(self):
        results = self._search([1.0, 0.0], [2])
        assert len(results) == 1
        assert results[0]["metadata"]["department_id"] == 2

    def test_no_department_filter_returns_all(self):
        results = self._search([1.0, 0.0], [])
        assert len(results) == 1
        assert results[0]["filename"] == "policy.txt"

    def test_top_k_limits_results(self):
        results = self._search([1.0, 0.0], [], top_k=1)
        assert len(results) == 1

    def test_returns_sorted_by_score_desc(self):
        results = self._search([1.0, 0.0], [], top_k=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_zero_vector_returns_empty(self):
        results = self._search([0.0, 0.0], [])
        assert results == []


class TestRowsToResults:
    class FakeRow:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def test_maps_fields(self):
        row = self.FakeRow(
            document_id=5,
            original_filename="doc.txt",
            chunk_index=2,
            text="content",
            metadata={"department_id": 2},
            score=0.87,
        )
        result = _rows_to_results([row])
        assert result[0]["document_id"] == 5
        assert result[0]["filename"] == "doc.txt"
        assert result[0]["chunk_index"] == 2
        assert result[0]["text"] == "content"
        assert result[0]["score"] == 0.87

    def test_none_score_defaults_zero(self):
        row = self.FakeRow(document_id=1, original_filename="a.txt", chunk_index=0, text="t", metadata={}, score=None)
        result = _rows_to_results([row])
        assert result[0]["score"] == 0.0
