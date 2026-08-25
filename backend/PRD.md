# Product Requirements Document: Enterprise Knowledge Assistant (EKA)

## 1. Overview

**Project Name:** Enterprise Knowledge Assistant (EKA)

**Elevator Pitch:** An enterprise-grade Retrieval-Augmented Generation (RAG) platform that allows employees to securely search and chat with company knowledge while enforcing strict Role-Based Access Control (RBAC). Documents are ingested asynchronously, indexed into a vector database, filtered by user permissions, and provided to an LLM to generate accurate, permission-aware responses.

**Goal:** Demonstrate production-level backend engineering including authentication, authorization, async pipelines, distributed systems, vector databases, AI orchestration, monitoring, testing, Docker deployment, CI/CD, and scalable architecture.

## 2. Users & Personas

| Role | Capabilities |
|------|-------------|
| **Employee** | Login, upload allowed documents, chat, search documents, view own uploads |
| **Manager** | Everything Employee, plus upload department knowledge |
| **Admin** | Everything, plus manage users, manage departments, delete documents, view audit logs, view monitoring dashboard |

## 3. Functional Requirements

### 3.1 Authentication
- FR-001: Users shall register with name, email, password, department, and role
- FR-002: Users shall log in with email and password
- FR-003: The system shall issue JWT access tokens (30min expiry)
- FR-004: The system shall issue refresh tokens (7 day expiry)
- FR-005: All authenticated endpoints shall validate JWT tokens
- FR-006: Passwords shall be hashed using bcrypt

### 3.2 Authorization
- FR-007: The system shall enforce RBAC at the endpoint level
- FR-008: The system shall filter search results by department membership
- FR-009: Employees shall only see documents from their own department
- FR-010: Managers shall see department documents plus their own uploads
- FR-011: Admins shall see all documents

### 3.3 Document Management
- FR-012: Users shall upload documents (PDF, DOCX, MD, CSV, XLSX, TXT)
- FR-013: Uploads shall be validated for file type and size (max 10MB)
- FR-014: Uploads shall trigger async processing pipeline
- FR-015: Documents shall report status: pending, processing, ready, failed
- FR-016: Users shall list their uploaded documents
- FR-017: Admins shall delete any document
- FR-018: Documents shall be assigned to the uploader's department

### 3.4 RAG Pipeline
- FR-019: The system shall parse document content based on file type
- FR-020: The system shall chunk text using recursive character splitting
- FR-021: Chunks shall overlap by 200 characters
- FR-022: Each chunk shall be embedded using vector embeddings
- FR-023: Embeddings shall be stored in a vector database (PGVector / local fallback)

### 3.5 Search
- FR-024: Users shall search documents by natural language query
- FR-025: Search shall return top-K results with similarity scores
- FR-026: Search results shall be filtered by user's authorized departments
- FR-027: Search shall use cosine similarity
- FR-028: Results shall include document source, chunk text, and confidence score

### 3.6 Chat
- FR-029: Users shall ask questions in natural language
- FR-030: The system shall retrieve relevant context using vector search
- FR-031: The system shall generate answers using an LLM (Gemini / Groq / fallback)
- FR-032: Answers shall cite sources (document filename, chunk index)
- FR-033: Answers shall include a confidence score
- FR-034: Chat sessions shall maintain conversation history
- FR-035: Users shall view their chat history and past messages

## 4. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Chat Response Time | < 3 seconds |
| Search Response Time | < 500ms |
| Upload Processing | Background (async) |
| Availability | 99% |
| Document Capacity | 100,000 |
| User Capacity | 10,000 |
| Concurrent Requests | 500+ |
| Chunk Size | 1,000 characters |
| Chunk Overlap | 200 characters |
| Top-K Retrieval | 5 |
| Similarity Threshold | 0.7 |

## 5. Constraints
- Must use PostgreSQL with PGVector as primary vector store
- Must support local-only mode (no external API dependencies)
- Must be deployable via Docker Compose
- Must include monitoring (Prometheus + Grafana)
- All secrets via environment variables only

## 6. Future Considerations
- Multi-tenant architecture
- SSO (Azure AD, Google Workspace)
- Hybrid lexical + semantic search
- Knowledge graph integration
- Streaming responses
- Document versioning
- Multi-modal support
- Agentic workflows
- Kubernetes deployment
