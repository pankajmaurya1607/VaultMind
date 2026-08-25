# Enterprise Knowledge Assistant (EKA)

An enterprise-grade Retrieval-Augmented Generation (RAG) platform built with FastAPI, PostgreSQL+PGVector, Celery, and AI orchestration. Allows employees to securely search and chat with company knowledge while enforcing strict Role-Based Access Control (RBAC).

## Features

- **🔐 Authentication** - HttpOnly-cookie sessions (with Bearer fallback for API clients), token rotation + revocation blacklist, CSRF guard, bcrypt hashing
- **👥 RBAC** - Role-based (Admin, Manager, Employee) and department-level document access control, enforced at the database query level
- **📄 Document Management** - Streamed uploads with magic-byte content validation; parse, chunk, and index PDF, DOCX, MD, CSV, XLSX, TXT
- **🔍 Vector Search** - Semantic search with cosine similarity (HNSW-indexed PGVector), department-filtered results
- **💬 AI Chat** - Context-aware answers with source citations and confidence scoring
- **⚡ Async Pipeline** - Celery workers for background document processing; beat scheduler for metrics refresh and blacklist pruning
- **📊 Monitoring** - Prometheus metrics + alert rules, Grafana dashboards provisioned as code, structured audit trail
- **🐳 Docker** - Full Docker Compose stack including an nginx-served frontend (same-origin API proxy)

## Quick Start

```bash
# Configure
cp .env.example .env   # set SECRET_KEY (+ optional GEMINI/GROQ keys)

# Start all services (migrations apply automatically on backend boot)
docker compose up -d --build

# Seed roles, departments, and the admin user
docker compose exec backend python seed_data.py

# UI: http://localhost      API: http://localhost:8000/health
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

- **Backend:** FastAPI, Python 3.12, Uvicorn
- **Database:** PostgreSQL 16 + PGVector (HNSW), SQLAlchemy 2.0 async, Alembic
- **Queue:** Celery + Redis, Flower
- **AI:** Gemini (primary LLM), Groq Llama-3.1 (secondary), local BGE-small embeddings fallback
- **Frontend:** React 19 + TypeScript + Vite, Tailwind CSS v4, TanStack Query
- **Monitoring:** Prometheus + Grafana (provisioned as code)
- **Testing:** Pytest (unit/integration/RBAC matrix/security), Vitest + Playwright
- **Deployment:** Docker, Docker Compose, GitHub Actions CI

## Architecture

```
Browser → nginx (:80, SPA + /api proxy) → FastAPI → Auth/CSRF/Rate-limit → Services → PGVector → LLM
                                              ↓
                                    Redis/Celery workers → parse → chunk → embed → index
```

## License

MIT
