# Deployment Guide: Enterprise Knowledge Assistant

## 1. Local Development

### Prerequisites
- Python 3.12+
- PostgreSQL 16 (with pgvector)
- Redis 7+

### Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn app.main:app --reload
```

### Seed Data
```bash
python seed_data.py
# Creates: Admin, Manager, Employee roles
# Creates: Finance, HR, Engineering, Sales, Marketing departments
# Creates: admin@eka.com / admin123 admin user
```

## 2. Docker Deployment

### Prerequisites
- Docker 24+
- Docker Compose v2+

### Quick Start
```bash
# Clone and configure
git clone <repo>
cd eka
cp .env.example .env   # then fill in SECRET_KEY and API keys

# Start all services (backend auto-applies migrations on boot)
docker compose up -d

# Seed the database (roles, departments, admin user)
docker compose exec backend python seed_data.py

# UI is served at http://localhost (nginx proxies /api to the backend)
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| frontend | 80 | nginx serving the React SPA, proxying `/api` to the backend |
| backend | 8000 | FastAPI application |
| postgres | 5432 | PostgreSQL + PGVector |
| redis | 6379 | Redis (queue + cache) |
| celery_worker | - | Async task processing |
| celery_beat | - | Periodic tasks (metrics refresh, token-blacklist pruning) |
| flower | 5555 | Celery monitoring |
| prometheus | 9090 | Metrics collection + alert rules |
| grafana | 3000 | Dashboards (provisioned as code from `grafana/`) |

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"admin@eka.com","password":"admin123"}'
```

## 3. Production Deployment

### Environment Variables (Required)
```bash
SECRET_KEY=<random-64-char-string>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/eka_db
DATABASE_URL_SYNC=postgresql+psycopg2://user:pass@host:5432/eka_db
REDIS_URL=redis://host:6379/0
GEMINI_API_KEY=<primary LLM - required for cloud chat>
GROQ_API_KEY=<secondary/optional>
ENVIRONMENT=production
```

### Production Checklist
- [ ] Strong SECRET_KEY (64+ chars, generated via `openssl rand -hex 32`)
- [ ] PostgreSQL with SSL enabled
- [ ] Redis with password authentication
- [ ] File uploads on persistent volume
- [ ] Reverse proxy (nginx/caddy) with SSL termination
- [ ] Rate limiting tuned for production
- [ ] Monitoring alerts configured
- [ ] Backup strategy for PostgreSQL
- [ ] Log aggregation (ELK/Loki)
- [ ] Health check endpoints monitored

### Scaling
- Increase Uvicorn workers: `--workers 8`
- Increase Celery workers: `--concurrency 8`
- Add read replicas for PostgreSQL
- Use Redis Sentinel for HA Redis
- Deploy behind a load balancer

## 4. CI/CD (GitHub Actions)

### Workflow: `.github/workflows/ci.yml`

```yaml
Triggers:
  - push to main
  - pull requests to main

Steps:
  1. Checkout code
  2. Set up Python 3.12
  3. Install dependencies
  4. Run linting (ruff, mypy)
  5. Run unit tests
  6. Run integration tests
  7. Build Docker images
  8. Push to registry
  9. Deploy to staging
```

## 5. Monitoring Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| High Latency | p95 chat > 5s | Page on-call |
| Error Rate | > 1% errors | Investigate |
| Queue Backlog | > 1000 queued tasks | Scale workers |
| Disk Space | < 20% free | Clean old uploads |
| DB Connections | > 80% of max | Scale DB |
