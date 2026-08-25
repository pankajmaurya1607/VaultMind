# API Specification: Enterprise Knowledge Assistant

**Base URL:** `/api/v1`

## Authentication

Two equivalent mechanisms are supported on every authenticated endpoint:

1. **HttpOnly cookies (browser/SPA flow)** — `POST /auth/login|register|refresh` set
   `eka_access` (~30 min) and `eka_refresh` (7 days, path `/api/v1/auth`) as
   `HttpOnly; SameSite=Lax; Secure` (Secure only in production) cookies.
2. **Bearer header (API clients/scripts)** — `Authorization: Bearer <access_token>`.
   An explicit header always takes precedence over cookies.

**CSRF guard:** state-changing requests authenticated *via cookie* must send the
custom header `X-Requested-With: XMLHttpRequest` (cross-site attackers cannot set
custom headers). Requests carrying an `Authorization` header and all `/auth/*`
endpoints are exempt.

### POST /auth/register
Register a new user. Roles are assigned server-side — every self-registration
creates an **Employee**; Admins change roles via `PATCH /users/{id}`.
Passwords require min 8 chars with at least one letter and one digit.

**Request Body:**
```json
{
  "name": "string",
  "email": "string",
  "password": "string",
  "department_id": "integer"
}
```

**Response (200):** sets auth cookies and returns tokens
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

### POST /auth/login
Authenticate with email + password. Sets auth cookies.

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
Rotate tokens. Reads the refresh token from the cookie first, then falls back to
the JSON body or `Authorization` header. Blacklists the presented refresh token
and the current access token (cookie flow).

**Request Body:** optional (`{"refresh_token": "string"}` for non-cookie clients)

**Response (200):** new token pair + refreshed cookies

### POST /auth/logout
Blacklist the presented access/refresh tokens and clear auth cookies.

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

## Users

### GET /users/me
Get current user profile (cookie or bearer auth).

### GET /users
List all users (Admin only). **Paginated.**

**Query Parameters:** `skip=0&limit=100`

**Response (200):**
```json
{
  "items": [ { "...user fields": "" } ],
  "total": "integer",
  "skip": "integer",
  "limit": "integer"
}
```

### PATCH /users/:id
Update user name / department / role (Admin only).

## Departments

### GET /departments
List departments (any authenticated user).

### GET /departments/roles
List roles (any authenticated user).

## Documents

### POST /documents
Upload a document. Files are streamed to disk with the size cap enforced
per-chunk and validated against magic-byte content signatures.

**Body:** `multipart/form-data` with `file` field (max 10MB)

**Supported types:** PDF, DOCX, MD, CSV, XLSX, TXT

**Errors:** `400` unsupported extension / empty file / content-type mismatch,
`413` file too large

**Response (200):**
```json
{
  "id": "integer",
  "filename": "string",
  "status": "pending"
}
```

### GET /documents
List documents (own uploads for users; all for Admin). **Paginated.**

**Query Parameters:** `skip=0&limit=100`

**Response (200):**
```json
{
  "items": [
    {
      "id": "integer",
      "original_filename": "string",
      "file_size": "integer",
      "mime_type": "string",
      "status": "pending | processing | ready | failed",
      "uploaded_by": "integer",
      "department_id": "integer",
      "chunk_count": "integer",
      "error_message": "string | null",
      "created_at": "datetime"
    }
  ],
  "total": "integer",
  "skip": "integer",
  "limit": "integer"
}
```

### GET /documents/:id
Get document details (owner or Admin).

### DELETE /documents/:id
Delete a document, its chunks, and stored file (Admin only). Writes an audit row;
non-admin attempts write an `rbac_denied` audit event.

## Search

### POST /search
Semantic vector search scoped to the caller's department(s).

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
Send a message and get an AI-generated answer with citations.

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
List the user's chat sessions with message counts.

### GET /chat/history/:session_id
Messages for a specific session (owner only; foreign sessions return empty).

## Admin

### GET /admin/metrics
System metrics (Admin only).

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
Audit logs (Admin only). **Paginated.**

**Query Parameters:** `skip=0&limit=100`

### GET /admin/departments
List departments (Admin only).

### GET /admin/roles
List roles (Admin only).

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
Prometheus metrics endpoint (no auth).

## Audit Events

The following actions are recorded in `audit_logs`: `register`, `login`,
`login_failed`, `logout`, `upload`, `delete`, `rbac_denied`. Query them via
`GET /admin/audit`.
