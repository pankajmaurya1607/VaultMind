from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram(
    "http_request_duration_ms",
    "HTTP request latency in ms",
    ["method", "endpoint"],
    buckets=[5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
)
CHAT_LATENCY = Histogram(
    "chat_response_duration_ms",
    "Chat response latency in ms",
    buckets=[100, 250, 500, 1000, 2500, 5000, 10000],
)
LLM_LATENCY = Histogram(
    "llm_response_duration_ms",
    "LLM response latency in ms",
    buckets=[100, 250, 500, 1000, 2500, 5000, 10000],
)
SEARCH_LATENCY = Histogram(
    "search_duration_ms",
    "Search latency in ms",
    buckets=[10, 25, 50, 100, 250, 500, 1000],
)
EMBEDDING_LATENCY = Histogram(
    "embedding_duration_ms",
    "Embedding latency in ms",
    buckets=[10, 25, 50, 100, 250, 500, 1000],
)
QUEUE_SIZE = Gauge("celery_queue_size", "Celery task queue size")
ACTIVE_USERS = Gauge("active_users", "Number of active users")
DOCUMENTS_TOTAL = Gauge("documents_total", "Total number of documents", ["status"])
TOKENS_USED = Counter("tokens_used_total", "Total tokens used", ["model"])
