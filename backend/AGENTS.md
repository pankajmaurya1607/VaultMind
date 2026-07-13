# Agent Instructions: Enterprise Knowledge Assistant

This file provides context and instructions for AI coding agents working on this project.

## Project Overview

Enterprise Knowledge Assistant (EKA) is a production-grade RAG platform built with FastAPI. It enables secure document search and chat across company knowledge with strict RBAC enforcement.

## Repository Structure

```
backend/
├── app/
│   ├── api/          # Route handlers (auth, users, documents, search, chat, admin)
│   ├── auth/         # JWT, password hashing, auth dependencies
│   ├── config/       # Settings via pydantic-settings
│   ├── core/         # Exception handlers
│   ├── db/           # SQLAlchemy async engine, session, Base
│   ├── mid/          # Middleware (logging, rate limiting)
│   ├── models/       # SQLAlchemy ORM models
│   ├── monitoring/   # Prometheus metrics
│   ├── rag/          # RAG pipeline (embeddings, retriever, LLM)
│   ├── rbac/         # Role-based access control
│   ├── repositories/ # Data access layer
│   ├── schemas/      # Pydantic request/response schemas
│   ├── services/     # Business logic layer
│   ├── tasks/        # Celery async tasks
│   └── workers/      # Celery app configuration
├── tests/            # Unit, integration, API, worker tests
├── docs/             # Additional documentation
├── PRD.md            # Product requirements
├── ARCHITECTURE.md   # System architecture
├── API_SPEC.md       # API specification
├── DATABASE.md       # Database design
├── SECURITY.md       # Security documentation
├── TESTING.md        # Testing strategy
└── DEPLOYMENT.md     # Deployment guide
```

## Key Conventions

### Code Style
- Type hints required on all functions
- Async/await throughout (FastAPI + SQLAlchemy async)
- Service layer pattern (API → Service → Repository → Model)
- JSON for all API responses
- UUID for stored filenames

### Naming
- Endpoints: plural nouns (`/documents`, `/users`)
- Services: `XxxService`
- Repositories: `XxxRepository`
- Models: Singular, PascalCase
- Schemas: `XxxRequest`, `XxxResponse`

### Error Handling
- HTTP exceptions with standard status codes
- Global exception handler for unhandled errors
- Validation errors return 422 with field details
- Service layer raises HTTPException for business logic errors

### Database
- AsyncSession for all database operations
- Flush (not commit) after mutations in repositories
- Commit at session lifecycle end (get_db dependency)
- Rollback on exception

### Dependencies
- `get_db` for database sessions
- `get_current_user` for authenticated endpoints
- Role checkers for authorization
- Inject via FastAPI Depends

## Task Execution Guidelines

1. Read the relevant files before making changes
2. Follow existing patterns for service/repository/API layers
3. Add type hints to all new functions
4. Add tests for new functionality
5. Update API_SPEC.md when adding/changing endpoints
6. Run linting before committing (`ruff check .`)
7. Verify tests pass (`pytest tests/ -v`)

## Environment
- Python 3.12+
- PostgreSQL 16 with pgvector
- Redis 7+
- See `.env.example` for all configuration options

## Decision Records
See `decisions/` directory for Architecture Decision Records (ADRs).
