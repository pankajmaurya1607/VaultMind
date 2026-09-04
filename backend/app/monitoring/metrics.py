"""Lightweight no-op metrics (prometheus_client removed for demo slimness).

Same names/API as before so all call sites keep working; only the
in-memory search-latency stats used by MonitoringService retain state.
"""


class _NoopMetric:
    def labels(self, *args, **kwargs):
        return self

    def observe(self, *args, **kwargs):
        pass

    def inc(self, *args, **kwargs):
        pass

    def dec(self, *args, **kwargs):
        pass

    def set(self, *args, **kwargs):
        pass


REQUEST_COUNT = _NoopMetric()
REQUEST_LATENCY = _NoopMetric()
CHAT_LATENCY = _NoopMetric()
LLM_LATENCY = _NoopMetric()
SEARCH_LATENCY = _NoopMetric()
EMBEDDING_LATENCY = _NoopMetric()
QUEUE_SIZE = _NoopMetric()
ACTIVE_USERS = _NoopMetric()
DOCUMENTS_TOTAL = _NoopMetric()
TOKENS_USED = _NoopMetric()

_search_latency = {"sum_ms": 0.0, "count": 0}


def record_search_latency(latency_ms: float) -> None:
    _search_latency["sum_ms"] += latency_ms
    _search_latency["count"] += 1


def search_latency_stats() -> tuple[float, int]:
    count = _search_latency["count"]
    if count == 0:
        return 0.0, 0
    return round(_search_latency["sum_ms"] / count, 2), count
