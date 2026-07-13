# Architecture Document: Enterprise Knowledge Assistant

## System Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Browser   │────▶│   FastAPI   │────▶│  PostgreSQL  │
│  (Client)   │     │  (Uvicorn)  │     │  + PGVector  │
└─────────────┘     └──────┬──────┘     └──────────────┘
                           │                      │
                           │                      │
                    ┌──────▼──────┐      ┌────────▼────────┐
                    │    Redis    │◀────▶│ Celery Workers  │
                    │  (Queue)    │      │ (Parse, Chunk,  │
                    └─────────────┘      │  Embed, Store)  │
                                          └────────────────┘
                           │
                    ┌──────▼──────┐
                    │  AI Services│
                    │ ┌─────────┐ │
                    │ │OpenAI   │ │
                    │ │Groq     │ │
                    │ │Sentence │ │
                    │ │Transform│ │
                    │ └─────────┘ │
                    └─────────────┘
```

## Component Responsibilities

### 1. API Layer (FastAPI)
- HTTP interface for all client interactions
- Request validation via Pydantic schemas
- Authentication middleware (JWT validation)
- Rate limiting middleware
- Request logging middleware
- Prometheus metrics endpoint

### 2. Auth Service
- User registration and login
- JWT access + refresh token management
- Password hashing (bcrypt)
- Token validation and decoding

### 3. RBAC Service
- Role-based endpoint authorization
- Department-based document filtering
- Admin / Manager / Employee permission hierarchy

### 4. Document Service
- File upload with validation (type, size, MIME)
- Async processing via Celery
- Status tracking (pending → processing → ready / failed)
- File storage on local filesystem

### 5. RAG Pipeline

```
Upload → Validation → Celery Queue → Parser → Chunker → Embedder → Vector Store
```

- **Parser:** Extracts text from PDF, DOCX, MD, CSV, XLSX, TXT
- **Chunker:** Recursive character splitting (1000 chars, 200 overlap)
- **Embedder:** OpenAI text-embedding-3-small (fallback: BAAI/bge-small-en-v1.5)
- **Vector Store:** PGVector (fallback: in-memory numpy store)

### 6. Retriever
- Cosine similarity search
- Department-based RBAC filter on results
- Top-K retrieval (default: 5)
- Similarity threshold (default: 0.7)

### 7. LLM Generator
- Context-aware answer generation
- Source citation enforcement
- Confidence scoring (average similarity)
- Providers: OpenAI GPT-4o-mini → Groq Llama-3.1 → Fallback template

### 8. Chat Service
- Session management (create, retrieve)
- Message history persistence
- Source tracking per message
- Token usage and latency tracking

### 9. Monitoring
- Prometheus metrics (request count, latency, tokens, queue size)
- Logging middleware (every request, auth event, search, RBAC denial)
- System metrics endpoint (admin only)

### 10. Celery Workers
- Async document processing
- Retry logic (3 retries, 60s delay)
- Status updates to database
- Embedding storage

## Data Flow

### Document Upload Flow
```
POST /documents → Validate file → Save to disk → Create DB record → 
Enqueue Celery task → Return 200 {id, status: "pending"} →
Worker: Read file → Parse → Chunk → Embed → Store vectors → 
Update status to "ready"
```

### Chat Flow
```
POST /chat → Validate JWT → Get user department → 
Embed question → PGVector search (filtered by dept) → 
Retrieve top-K chunks → Build context → Call LLM → 
Store messages → Return {answer, sources, confidence}
```

### Search Flow
```
POST /search → Validate JWT → Get user department → 
Embed query → Vector search with RBAC filter → 
Return ranked results with scores
```

## Scaling Considerations
- **Database:** Connection pooling (20 pool, 10 overflow)
- **Workers:** Horizontal scaling of Celery workers
- **Caching:** Redis for rate limiting and task queue
- **API:** 4 Uvicorn workers per container
- **Vector Search:** PGVector with HNSW index for fast approximate nearest neighbor
