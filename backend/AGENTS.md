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

---

## AI Workspace (.ai/)

This project includes a standardized **AI Workspace** at the repository root (`.ai/`) to provide persistent external memory for AI coding assistants. To maintain context across sessions, **read the following on every new session start**:

### Session Start Protocol
1. **Read** `.ai/docs/00_PROJECT.md` — project identity, vision, and scope
2. **Read** `.ai/current_state.md` — current operational state and completion
3. **Read** `.ai/roadmap/03_ROADMAP.md` — current phase and upcoming deliverables
4. **Read** `.ai/docs/11_CONTEXT.md` — quick context summary for LLM injection

### Reference Files (read as needed)
- `.ai/docs/01_REQUIREMENTS.md` — all functional and non-functional requirements
- `.ai/docs/02_ARCHITECTURE.md` — system architecture, data flow, scaling plan
- `.ai/decisions/05_DECISIONS.md` — architecture decision log (ADRs)
- `.ai/docs/06_TECH_STACK.md` — technology stack specification
- `.ai/docs/07_FILE_INDEX.md` — file-purpose/dependency index
- `.ai/docs/08_API.md` — API endpoint reference
- `.ai/docs/09_DATABASE.md` — database schema and indexes
- `.ai/prompts/` — AI prompt library (system, chat, eval templates)
- `.ai/schemas/pydantic_schemas.md` — Pydantic request/response schema reference

### Machine-Readable Files (for automated agent parsing)
- `.ai/project.yaml` — canonical project metadata
- `.ai/current_state.yaml` — operational state
- `.ai/roadmap/roadmap.yaml` — roadmap phases
- `.ai/decisions/decisions.yaml` — decision log
- `.ai/tasks/tasks.yaml` — task tracking
- `.ai/docs/file_map.json` — file index with dependencies
- `.ai/graphs/dependency_graph.json` — module dependency graph
- `.ai/graphs/architecture.mmd` — system architecture diagram
- `.ai/graphs/dependency.mmd` — dependency topology diagram
- `.ai/graphs/workflow.mmd` — sequence workflow diagram

### Session End Protocol
Before ending a session, update:
1. `.ai/current_state.md` — refresh completion percentage and next tasks
2. `.ai/tasks/todo.md` / `doing.md` / `done.md` — move completed tasks
3. `.ai/tasks/changelog/YYYY-MM-DD.md` — log completed work, files changed, problems, solutions
4. `.ai/decisions/05_DECISIONS.md` — add any new architectural decisions
5. `.ai/current_state.yaml` — update machine-readable state
