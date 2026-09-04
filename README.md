# VaultMind — Minimal RAG + RBAC

A lean Retrieval-Augmented Generation platform built for fast deployment: FastAPI + PostgreSQL+PGVector (384-dim BGE) + Celery/Redis + single LLM (Gemini or Groq). Upload → chunk → embed → retrieve → chat with strict Role-Based Access Control.

## Features (core RAG+RBAC only)

- **🔐 Auth** - Bearer JWT (with HttpOnly cookie fallback), bcrypt, token blacklist
- **👥 RBAC** - Roles Admin/Manager/Employee + department isolation at SQL level
- **📄 Documents** - Streamed uploads (10 MB), PDF/DOCX/TXT/MD → Celery parse/chunk/embed
- **🔍 Vector Search** - Cosine similarity HNSW PGVector, dept-filtered, parameterized SQL
- **💬 Chat** - Context-aware answers with citations + confidence; `asyncio.to_thread` offload
- **⚡ Async** - Celery worker `document_processing` queue, 4 concurrency, retry 3×
- **🐳 Deploy** - 5 services only (postgres, redis, backend, worker, nginx frontend) — 2-command boot

## Quick Start (2 commands)

```bash
cp .env.example .env   # set SECRET_KEY for prod, optional GEMINI/GROQ keys
docker compose up -d --build   # auto: migrate → seed → serve

# UI: http://localhost      API: http://localhost/api/v1    Health: http://localhost/health
```

Default admin: `admin@eka.com` / `admin123` — change it immediately.

## Documentation

| Document | Description |
|----------|-------------|
| [PRD](backend/PRD.md) | Product requirements and specifications |
| [Architecture](backend/ARCHITECTURE.md) | System architecture and component design |
| [API Spec](backend/API_SPEC.md) | Complete API reference |
| [Database](backend/DATABASE.md) | Database schema and migration strategy |
| [Security](backend/SECURITY.md) | Security architecture and threat model |
| [Testing](backend/TESTING.md) | Testing strategy and procedures |
| [Deployment](backend/DEPLOYMENT.md) | Deployment and operations guide |
| [Agent Guide](backend/AGENTS.md) | Instructions for AI coding agents |

## Tech Stack

- **Backend:** FastAPI, Python 3.12, Uvicorn (2 workers)
- **Database:** PostgreSQL 16 + PGVector HNSW 384-dim, SQLAlchemy 2.0 async, Alembic
- **Queue:** Celery + Redis (single worker, `document_processing` queue)
- **AI:** BGE-small-en-v1.5 embeddings (local) + Groq/Gemini single LLM + fallback template
- **Frontend:** React 19 + TypeScript + Vite, Tailwind v4, TanStack Query, nginx :80 proxy
- **Testing:** Pytest, Vitest + Playwright
- **Deploy:** Docker Compose (5 services), GitHub Actions CI (smoke test)

## Architecture

```
Browser → nginx :80 (SPA + /api proxy) → FastAPI → Services → PGVector → LLM
                                           ↓
                                 Redis → Celery worker → parse → chunk → embed → index
```

## License

MIT
