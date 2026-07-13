# API Specification: Enterprise Knowledge Assistant

**Base URL:** `/api/v1`

## Authentication

### POST /auth/register
Register a new user.

**Request Body:**
```json
{
  "name": "string",
  "email": "string",
  "password": "string",
  "department_id": "integer",
  "role_id": "integer (default: 3)"
}
```

**Response (201):**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

### POST /auth/login
Authenticate and receive tokens.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

### POST /auth/refresh
Refresh an expired access token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### POST /auth/logout
Invalidate the current session.

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

## Users

### GET /users/me
Get current user profile.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "integer",
  "name": "string",
  "email": "string",
  "department_id": "integer",
  "department_name": "string",
  "role_id": "integer",
  "role_name": "string",
  "created_at": "datetime"
}
```

### GET /users
List all users (Admin only).

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:** `skip=0&limit=100`

### PATCH /users/:id
Update user (Admin only).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "string (optional)",
  "department_id": "integer (optional)",
  "role_id": "integer (optional)"
}
```

## Documents

### POST /documents
Upload a document.

**Headers:** `Authorization: Bearer <token>`

**Body:** `multipart/form-data` with `file` field

**Supported types:** PDF, DOCX, MD, CSV, XLSX, TXT

**Response (200):**
```json
{
  "id": "integer",
  "filename": "string",
  "status": "pending",
  "message": "Document uploaded successfully"
}
```

### GET /documents
List user's documents (all if Admin).

**Headers:** `Authorization: Bearer <token>`

### GET /documents/:id
Get document details.

**Headers:** `Authorization: Bearer <token>`

### DELETE /documents/:id
Delete a document (Admin only).

**Headers:** `Authorization: Bearer <token>`

## Search

### POST /search
Search documents by natural language query.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query": "string",
  "top_k": "integer (default: 5)"
}
```

**Response (200):**
```json
{
  "results": [
    {
      "document_id": "integer",
      "filename": "string",
      "chunk_index": "integer",
      "text": "string",
      "score": "float",
      "metadata": {}
    }
  ],
  "total": "integer"
}
```

## Chat

### POST /chat
Send a message and get an AI-generated response.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "session_id": "integer (optional, null for new session)",
  "question": "string"
}
```

**Response (200):**
```json
{
  "session_id": "integer",
  "answer": "string",
  "sources": [
    {
      "document_id": "integer",
      "filename": "string",
      "chunk_index": "integer",
      "text": "string",
      "score": "float"
    }
  ],
  "confidence_score": "float",
  "tokens_used": "integer",
  "latency_ms": "integer"
}
```

### GET /chat/history
List user's chat sessions.

**Headers:** `Authorization: Bearer <token>`

### GET /chat/history/:session_id
Get messages for a specific session.

**Headers:** `Authorization: Bearer <token>`

## Admin

### GET /admin/metrics
Get system metrics (Admin only).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "total_documents": "integer",
  "total_users": "integer",
  "total_chat_sessions": "integer",
  "documents_by_status": {},
  "total_tokens_used": "integer",
  "avg_chat_latency_ms": "float",
  "avg_search_latency_ms": "float",
  "error_count": "integer"
}
```

### GET /admin/audit
View audit logs (Admin only).

**Headers:** `Authorization: Bearer <token>`

## Health

### GET /health
Service health check.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "Enterprise Knowledge Assistant",
  "version": "1.0.0"
}
```

## Metrics

### GET /metrics
Prometheus metrics endpoint.

**Headers:** No auth required
