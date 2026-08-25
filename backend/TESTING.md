# Testing Strategy: Enterprise Knowledge Assistant

## 1. Test Pyramid

```
        ╱╲
       ╱ E2E ╲
      ╱────────╲
     ╱ Integration╲
    ╱──────────────╲
   ╱   Unit Tests    ╲
  ╱────────────────────╲
 ╱  Static Analysis     ╲
╱─────────────────────────╲
```

## 2. Unit Tests

### Location: `tests/unit/`
### Framework: pytest, pytest-asyncio
### Target: Isolated components

| Test Suite | File | What We Test |
|-----------|------|--------------|
| Auth | test_auth.py | Password hashing, JWT creation/validation, token expiry |
| Chunking | test_chunking.py | Text splitting, overlap, edge cases |
| Embedding | test_embedder.py | Embedding dimension, batch processing |
| Validation | test_validation.py | File type checks, size limits, schema validation |

**Run:** `pytest tests/unit -v`

## 3. Integration Tests

### Location: `tests/integration/`
### Target: API endpoints with real database

| Test Suite | File | What We Test |
|-----------|------|--------------|
| Auth API | test_auth_api.py | Register, login, duplicate emails, invalid credentials |
| Cookie Auth | test_cookie_auth.py | HttpOnly cookie issuance, refresh rotation, CSRF guard, logout |
| Document API | test_document_api.py | Upload (incl. content-signature + empty-file rejection), list, audit trail |
| Chat API | test_chat_api.py | Chat flow, search, history |
| RBAC Matrix | test_rbac_matrix.py | Role-based access, department filtering, cross-user denial |

**Run:** `pytest tests/integration -v`

## 4. Worker Tests

### Location: `tests/workers/`
### Target: Celery task processing

- Document parsing (PDF, DOCX, MD, TXT)
- Text chunking and embedding
- Worker error handling and retries
- Status transitions (pending → processing → ready/failed)

## 5. Security Tests

- SQL injection attempts
- JWT tampering
- Path traversal in file uploads
- Rate limit bypass
- Role escalation attempts

## 6. Performance / Load Tests

Using `locust` or `k6`:
- 500 concurrent users
- Mixed workload (80% chat, 20% upload)
- Response time percentiles (p50, p95, p99)
- Error rate monitoring

## 7. Evaluation Tests

Using Ragas framework:
- Context Precision
- Faithfulness
- Answer Relevancy
- Recall
- End-to-end latency

## 8. Running Tests

```bash
# All tests
pytest tests/ -v --cov=app --cov-report=term-missing

# Unit only
pytest tests/unit -v

# Integration only (requires running DB)
pytest tests/integration -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html
```

## 9. CI/CD Integration

Tests run automatically on:
- Push to `main` branch
- Pull requests to `main`
- Scheduled daily run for evaluation tests

**Required checks before merge:**
- All unit tests pass
- All integration tests pass
- Coverage >= 80%
- No linting errors
- Security scan passes
