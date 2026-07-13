# Enterprise Knowledge Assistant (EKA)

An enterprise-grade Retrieval-Augmented Generation (RAG) platform built with FastAPI, PostgreSQL+PGVector, Celery, and AI orchestration. Allows employees to securely search and chat with company knowledge while enforcing strict Role-Based Access Control (RBAC).

## Features

- **🔐 Authentication** - JWT-based auth with access/refresh tokens, bcrypt password hashing
- **👥 RBAC** - Role-based (Admin, Manager, Employee) and department-level document access control
- **📄 Document Management** - Upload, parse, chunk, and index PDF, DOCX, MD, CSV, XLSX, TXT
- **🔍 Vector Search** - Semantic search with cosine similarity, department-filtered results
- **💬 AI Chat** - Context-aware answers with source citations and confidence scoring
- **⚡ Async Pipeline** - Celery workers for background document processing
- **📊 Monitoring** - Prometheus metrics, Grafana dashboards, structured logging
- **🐳 Docker** - Full Docker Compose setup with all services

## Quick Start

```bash
# Start all services
docker compose up -d

# Seed database with roles, departments, and admin user
docker compose exec backend python seed_data.py

# Access the API
curl http://localhost:8000/health
```

Default admin: `admin@eka.com` / `admin123`

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
- **Database:** PostgreSQL 16 + PGVector
- **Queue:** Celery + Redis
- **AI:** LangChain, OpenAI, Groq, Sentence Transformers
- **Monitoring:** Prometheus, Grafana, OpenTelemetry
- **Testing:** Pytest, FactoryBoy, Ragas
- **Deployment:** Docker, Docker Compose, GitHub Actions

## Architecture

```
Client → FastAPI → Auth/RBAC Middleware → Redis/Celery → Workers → PGVector → LLM
```

## License

MIT
