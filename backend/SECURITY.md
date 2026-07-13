# Security Documentation: Enterprise Knowledge Assistant

## 1. Authentication

### Password Security
- Passwords hashed using bcrypt via `passlib`
- No plain-text password storage
- No password logging

### JWT Token Strategy
- **Access Token:** 30-minute expiry, contains user ID and type claim
- **Refresh Token:** 7-day expiry, used to obtain new access tokens
- **Algorithm:** HS256 with server-side secret key
- **Secret Key:** Must be set via `SECRET_KEY` environment variable (minimum 32 characters in production)

### Token Flow
```
1. Client authenticates → receives access + refresh tokens
2. Client sends access token in Authorization header
3. Server validates token (signature, expiry, type="access")
4. On 401, client uses refresh token to get new access token
5. Refresh token is validated (signature, expiry, type="refresh")
```

## 2. Authorization (RBAC)

### Role Hierarchy
| Role | Level | Access |
|------|-------|--------|
| Admin | 1 | Full system access |
| Manager | 2 | Department + own uploads |
| Employee | 3 | Own uploads only |

### Department-based Filtering
- All document queries and searches are filtered by department
- Employees only see documents where `department_id = user.department_id`
- Admins bypass department filtering
- Enforcement happens at the repository/service layer

### Endpoint Protection
- Public: `/auth/register`, `/auth/login`, `/health`, `/metrics`
- Authenticated: `/auth/refresh`, `/users/me`, `/documents`, `/chat`, `/search`
- Admin only: `/users` (list all), `/users/:id`, `/documents/:id` (delete), `/admin/*`

## 3. Input Validation

### File Upload Security
- Extension whitelist: `.pdf`, `.docx`, `.md`, `.csv`, `.xlsx`, `.txt`
- File size limit: 10MB (configurable)
- MIME type validation
- Files stored with UUID-based names (no path traversal)
- Upload directory outside application root

### API Inputs
- All request bodies validated by Pydantic schemas
- String length limits enforced
- SQL injection prevented by SQLAlchemy ORM parameterization
- XSS prevention via response serialization

## 4. Rate Limiting
- 60 requests per minute per IP address
- Implemented via in-memory sliding window
- Returns 429 Too Many Requests on breach

## 5. Audit Logging
Every security-relevant event is logged:
- User registration and login
- Document upload and deletion
- Failed authentication attempts
- RBAC denials
- All admin actions
- System errors

## 6. Environment Variables
All secrets are configured via environment variables:
- `SECRET_KEY` - JWT signing key
- `DATABASE_URL` - Database connection string
- `OPENAI_API_KEY` - OpenAI API key
- `GROQ_API_KEY` - Groq API key
- `REDIS_URL` - Redis connection string

## 7. Docker Security
- Non-root user recommended for production containers
- Secrets via environment variables (not in Dockerfile)
- Network isolation (internal networks for backend/db)
- Health checks for all services

## 8. Threat Model

| Threat | Mitigation |
|--------|-----------|
| Token theft | Short-lived access tokens, refresh token rotation |
| SQL injection | ORM parameterized queries |
| Path traversal | UUID filenames, extension whitelist |
| DoS | Rate limiting, connection pooling |
| Unauthorized document access | RBAC + department filtering |
| Prompt injection | Strict system prompt, context-only answers |
| LLM hallucination | Source citation requirement, confidence scoring |
