# Database Design: Enterprise Knowledge Assistant

## Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   roles     │     │ departments │     │    users    │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id (PK)     │     │ id (PK)     │     │ id (PK)     │
│ name        │     │ name        │     │ name        │
└──────┬──────┘     └──────┬──────┘     │ email       │
       │                   │            │ password_hash│
       │                   │            │ dept_id(FK) │
       └────────┬──────────┘            │ role_id(FK) │
                │                       │ created_at  │
                │                       └──────┬──────┘
                │                              │
         ┌──────▼──────┐              ┌────────▼────────┐
         │  documents  │              │ chat_sessions   │
         ├─────────────┤              ├─────────────────┤
         │ id (PK)     │              │ id (PK)         │
         │ filename    │              │ user_id (FK)    │
         │ original_fn │              │ title           │
         │ file_path   │              │ created_at      │
         │ file_size   │              └────────┬────────┘
         │ mime_type   │                       │
         │ uploaded_by │              ┌────────▼────────┐
         │ dept_id(FK) │              │    messages     │
         │ status      │              ├─────────────────┤
         │ chunk_count │              │ id (PK)         │
         │ error_msg   │              │ session_id (FK) │
         │ created_at  │              │ role            │
         └──────┬──────┘              │ content         │
                │                     │ sources (JSON)  │
         ┌──────▼──────┐              │ confidence      │
         │   chunks    │              │ tokens_used     │
         ├─────────────┤              │ latency_ms      │
         │ id (PK)     │              │ created_at      │
         │ doc_id (FK) │              └─────────────────┘
         │ text        │
         │ chunk_index │     ┌─────────────┐
         │ metadata    │     │  audit_logs │
         │ embedding   │     ├─────────────┤
         │ created_at  │     │ id (PK)     │
         └─────────────┘     │ user_id     │
                             │ user_email  │
                             │ action      │
                             │ resource    │
                             │ resource_id │
                             │ details     │
                             │ ip_address  │
                             │ success     │
                             │ created_at  │
                             └─────────────┘
```

## Migration Strategy

### Initial Schema
- Create roles table with seed data (Admin, Manager, Employee)
- Create departments table with seed data (Finance, HR, Engineering, Sales, Marketing)
- Create all remaining tables with foreign key constraints

### Vector Extension (PGVector)
- Requires PostgreSQL 16 with pgvector extension
- Vector column type: `vector(1536)` for OpenAI, `vector(384)` for local BGE model
- HNSW index on embedding column for fast ANN search:
  ```sql
  CREATE INDEX idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
  ```

### Future Migrations
- Add full-text search columns for hybrid search
- Add document versioning
- Add soft delete columns
- Add multi-tenant `organization_id` column

## Indexes
- `users.email` - unique index for login
- `chunks.document_id` - foreign key index
- `documents.uploaded_by` - user document listing
- `documents.department_id` - department filtering
- `documents.status` - status-based queries
- `chunks.embedding` - HNSW vector index
- `audit_logs.created_at` - time-based audit queries
