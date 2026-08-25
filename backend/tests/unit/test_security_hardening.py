"""Unit tests for Phase 3 security components: rate limiter behavior and
upload content-signature validation."""

from unittest.mock import MagicMock

import pytest

from app.mid.rate_limit import RateLimitMiddleware
from app.services.document import validate_content_signature

pytestmark = pytest.mark.unit


class TestLocalRateLimiter:
    def setup_method(self):
        self.limiter = RateLimitMiddleware(app=MagicMock())
        # Keep tests hermetic regardless of configured limit.
        self.limit = 3

    def _attempts(self, key, n):
        return [self.limiter._check_local(key, self.limit) for _ in range(n)]

    def test_allows_requests_under_limit(self):
        assert all(self._attempts("ip:a", self.limit - 1))

    def test_blocks_request_over_limit(self):
        results = self._attempts("ip:b", self.limit + 1)
        assert results[: self.limit] == [True] * self.limit
        assert results[self.limit] is False

    def test_window_expiry_restores_budget(self):
        import time

        key = "ip:c"
        self._attempts(key, self.limit)
        assert self.limiter._check_local(key, self.limit) is False
        # Age out the recorded timestamps.
        self.limiter._local_requests[key] = [time.time() - 61] * self.limit
        assert self.limiter._check_local(key, self.limit) is True

    def test_fallback_map_bounded_at_max_clients(self):
        from app.mid.rate_limit import _LOCAL_FALLBACK_MAX_CLIENTS

        for i in range(_LOCAL_FALLBACK_MAX_CLIENTS + 5):
            self.limiter._check_local(f"ip:{i}", 1000)
        assert len(self.limiter._local_requests) == _LOCAL_FALLBACK_MAX_CLIENTS
        # Oldest entries evicted first.
        assert "ip:0" not in self.limiter._local_requests
        assert f"ip:{_LOCAL_FALLBACK_MAX_CLIENTS + 4}" in self.limiter._local_requests


class TestClientIpResolution:
    def _request(self, xff=None, host="10.0.0.1"):
        request = MagicMock()
        request.headers = {"x-forwarded-for": xff} if xff else {}
        request.client.host = host
        return request

    def test_untrusted_proxy_ignores_xff(self, monkeypatch):
        monkeypatch.setattr("app.mid.rate_limit.settings.TRUST_PROXY_HEADERS", False)
        ip = RateLimitMiddleware._client_ip(self._request(xff="1.2.3.4"))
        assert ip == "10.0.0.1"

    def test_trusted_proxy_uses_leftmost_xff(self, monkeypatch):
        monkeypatch.setattr("app.mid.rate_limit.settings.TRUST_PROXY_HEADERS", True)
        ip = RateLimitMiddleware._client_ip(self._request(xff="1.2.3.4, 10.0.0.9"))
        assert ip == "1.2.3.4"

    def test_no_client_object_returns_unknown(self):
        request = MagicMock()
        request.headers = {}
        request.client = None
        assert RateLimitMiddleware._client_ip(request) == "unknown"


class TestContentSignature:
    def test_valid_pdf_magic(self):
        assert validate_content_signature(".pdf", b"%PDF-1.7 ...")

    def test_invalid_pdf_magic(self):
        assert not validate_content_signature(".pdf", b"Not a PDF at all")

    @pytest.mark.parametrize("ext", [".docx", ".xlsx"])
    def test_office_formats_require_zip_magic(self, ext):
        assert validate_content_signature(ext, b"PK\x03\x04rest")
        assert not validate_content_signature(ext, b"plain text")

    @pytest.mark.parametrize("ext", [".txt", ".md", ".csv"])
    def test_text_formats_reject_binary(self, ext):
        assert validate_content_signature(ext, b"hello world")
        assert not validate_content_signature(ext, b"bin\x00ary")

    def test_unknown_extension_passes_through(self):
        assert validate_content_signature(".xyz", b"anything")
