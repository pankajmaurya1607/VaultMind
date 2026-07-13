# Task 002: Database Models

## Objective
Create all SQLAlchemy ORM models matching the database design.

## Models
- Role (id, name)
- Department (id, name)
- User (id, name, email, password_hash, department_id, role_id, timestamps)
- Document (id, filename, original_filename, file_path, file_size, mime_type, uploaded_by, department_id, status, chunk_count, error_message, timestamps)
- Chunk (id, document_id, text, chunk_index, metadata, embedding_id, created_at)
- ChatSession (id, user_id, title, timestamps)
- Message (id, session_id, role, content, sources, confidence_score, tokens_used, latency_ms, created_at)
- AuditLog (id, user_id, user_email, action, resource, resource_id, details, ip_address, success, created_at)

## Key Decisions
- Use `DeclarativeBase` from SQLAlchemy 2.0
- All models in `app/models/`
- Proper foreign key relationships with back_populates
- Enum for DocumentStatus
- JSON column type for metadata and sources

## Definition of Done
- All models defined with proper types and constraints
- Relationships between models established
- Database tables created by `Base.metadata.create_all()`
