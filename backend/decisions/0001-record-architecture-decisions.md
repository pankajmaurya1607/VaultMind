# ADR 0001: Record Architecture Decisions

## Status
Accepted

## Context
We need to record architectural decisions made for the Enterprise Knowledge Assistant project to provide context for future developers and AI agents.

## Decision
We will use Architecture Decision Records (ADRs) as described by Michael Nygard. Each ADR will be a short markdown file in the `decisions/` directory.

## Consequences
- Easy to understand why decisions were made
- Provides context for AI agents
- Lightweight, no additional tooling required

---

# ADR 0002: Use FastAPI as Web Framework

## Status
Accepted

## Context
We need a Python web framework that supports async, has excellent performance, and strong typing.

## Decision
Use FastAPI for its async support, automatic OpenAPI docs, Pydantic integration, and performance.

## Consequences
- Automatic API documentation
- Type safety through Pydantic
- High performance (on par with Node.js/Go)

---

# ADR 0003: PostgreSQL with PGVector for Vector Storage

## Status
Accepted

## Context
We need a vector database for storing and searching embeddings.

## Decision
Use PostgreSQL with the PGVector extension rather than a separate vector database like Pinecone or Weaviate.

## Rationale
- Single database reduces operational complexity
- PGVector supports exact and approximate nearest neighbor search
- ACID compliance for metadata
- HNSW indexes for fast search

## Consequences
- Simplified infrastructure (no separate vector DB)
- Vector search performance may be lower than specialized solutions at very large scale
- Supports up to 100K+ documents comfortably

---

# ADR 0004: Celery for Async Task Processing

## Status
Accepted

## Context
Document processing (parsing, chunking, embedding) must happen asynchronously.

## Decision
Use Celery with Redis as broker for task queue.

## Rationale
- Mature, well-documented
- Supports task retries and monitoring (Flower)
- Redis is already in the stack

## Consequences
- Additional infrastructure (Redis, Celery workers)
- Task monitoring via Flower dashboard
- Supports horizontal scaling of workers

---

# ADR 0005: Repository Pattern for Data Access

## Status
Accepted

## Context
We need a clean separation between business logic and data access.

## Decision
Use the Repository pattern with a generic `BaseRepository<T>` and specific repositories for each entity.

## Rationale
- Testable data access layer
- Consistent interface for CRUD operations
- Easy to swap database implementations

## Consequences
- More files but clearer separation
- Reduced duplication of query logic

---

# ADR 0006: Free & Open Source AI Strategy

## Status
Accepted

## Context
The system needs embeddings and LLM responses but should work without external API dependencies and use free tools.

## Decision
Use free/open-source AI providers with automatic fallback:
- Embeddings: BAAI/bge-small-en-v1.5 (local, free) → Zero vectors
- LLM: Gemini 2.0 Flash (free tier) → Groq Llama-3.1 (free tier) → Template-based fallback

## Rationale
- All providers have free tiers or are completely free
- No API keys required for local embeddings
- Development possible without any API keys
- Graceful degradation

## Consequences
- Multiple code paths for AI operations
- Quality varies by provider
- Local mode has reduced capabilities
- No paid API dependencies
