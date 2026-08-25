import { http, HttpResponse } from "msw"

const API = "http://localhost:8000/api/v1"

export const handlers = [
  http.post(`${API}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string }
    if (body.email === "admin@eka.com" && body.password === "admin123") {
      return HttpResponse.json({
        access_token: "mock_access",
        refresh_token: "mock_refresh",
        token_type: "bearer",
      })
    }
    return HttpResponse.json({ detail: "Invalid credentials" }, { status: 401 })
  }),

  http.post(`${API}/auth/refresh`, () => {
    return HttpResponse.json({
      access_token: "mock_refreshed_access",
      refresh_token: "mock_refreshed_refresh",
      token_type: "bearer",
    })
  }),

  http.post(`${API}/auth/logout`, () => {
    return HttpResponse.json({ message: "Logged out successfully" })
  }),

  http.post(`${API}/auth/register`, async () => {
    return HttpResponse.json({
      access_token: "mock_access",
      refresh_token: "mock_refresh",
      token_type: "bearer",
    }, { status: 201 })
  }),

  http.get(`${API}/users/me`, () => {
    return HttpResponse.json({
      id: 1,
      name: "Admin User",
      email: "admin@eka.com",
      department_id: 1,
      department_name: "Engineering",
      role_id: 1,
      role_name: "Admin",
      created_at: new Date().toISOString(),
    })
  }),

  http.get(`${API}/users`, () => {
    return HttpResponse.json({
      items: [
        { id: 1, name: "Admin User", email: "admin@eka.com", department_id: 1, department_name: "Engineering", role_id: 1, role_name: "Admin", created_at: new Date().toISOString() },
        { id: 2, name: "Jane Doe", email: "jane@company.com", department_id: 1, department_name: "Engineering", role_id: 3, role_name: "Employee", created_at: new Date().toISOString() },
      ],
      total: 2,
      skip: 0,
      limit: 100,
    })
  }),

  http.patch(`${API}/users/:id`, async ({ params, request }) => {
    const updates = (await request.json()) as Partial<{ name: string; role_id: number; department_id: number }>
    return HttpResponse.json({ id: Number(params.id), name: updates.name ?? "Updated", email: "updated@company.com", department_id: updates.department_id ?? 1, department_name: "Engineering", role_id: updates.role_id ?? 2, role_name: "Manager", created_at: new Date().toISOString() })
  }),

  http.get(`${API}/departments`, () => {
    return HttpResponse.json([
      { id: 1, name: "Engineering" },
      { id: 2, name: "Marketing" },
      { id: 3, name: "Sales" },
    ])
  }),

  http.get(`${API}/departments/roles`, () => {
    return HttpResponse.json([
      { id: 1, name: "Admin" },
      { id: 2, name: "Manager" },
      { id: 3, name: "Employee" },
    ])
  }),

  http.get(`${API}/documents`, () => {
    return HttpResponse.json({
      items: [
        {
          id: 1,
          original_filename: "handbook.pdf",
          file_size: 102400,
          mime_type: "application/pdf",
          status: "ready",
          uploaded_by: 1,
          department_id: 1,
          chunk_count: 12,
          error_message: null,
          created_at: new Date().toISOString(),
        },
        {
          id: 2,
          original_filename: "report.csv",
          file_size: 20480,
          mime_type: "text/csv",
          status: "processing",
          uploaded_by: 1,
          department_id: 1,
          chunk_count: 0,
          error_message: null,
          created_at: new Date().toISOString(),
        },
      ],
      total: 2,
      skip: 0,
      limit: 100,
    })
  }),

  http.get(`${API}/documents/:id`, ({ params }) => {
    return HttpResponse.json({
      id: Number(params.id),
      original_filename: "handbook.pdf",
      file_size: 102400,
      mime_type: "application/pdf",
      status: "ready",
      uploaded_by: 1,
      department_id: 1,
      chunk_count: 12,
      error_message: null,
      created_at: new Date().toISOString(),
    })
  }),

  http.post(`${API}/documents`, async () => {
    return HttpResponse.json({ id: 3, filename: "new.pdf", status: "pending", message: "Document uploaded successfully" })
  }),

  http.delete(`${API}/documents/:id`, () => {
    return HttpResponse.json({ message: "Deleted" })
  }),

  http.post(`${API}/search`, async ({ request }) => {
    const body = (await request.json()) as { query: string }
    if (!body.query.trim()) {
      return HttpResponse.json({ results: [], total: 0 })
    }
    return HttpResponse.json({
      results: [
        {
          document_id: 1,
          filename: "handbook.pdf",
          chunk_index: 2,
          text: `This is a relevant result for query "${body.query}" with some highlighted content about onboarding.`,
          score: 0.92,
          metadata: {},
        },
      ],
      total: 1,
    })
  }),

  http.post(`${API}/chat`, async ({ request }) => {
    const body = (await request.json()) as { session_id: number | null; question: string }
    return HttpResponse.json({
      session_id: body.session_id ?? 1,
      answer: `Mock answer for: ${body.question}`,
      sources: [
        { document_id: 1, filename: "handbook.pdf", chunk_index: 0, text: "Source excerpt", score: 0.88 },
      ],
      confidence_score: 0.87,
      tokens_used: 42,
      latency_ms: 123,
    })
  }),

  http.get(`${API}/chat/history`, () => {
    return HttpResponse.json([
      { id: 1, title: "First conversation", created_at: new Date().toISOString(), message_count: 2 },
    ])
  }),

  http.get(`${API}/chat/history/:sessionId`, () => {
    return HttpResponse.json([
      { id: 1, role: "user", content: "Hello", sources: null, confidence_score: null, created_at: new Date().toISOString() },
      { id: 2, role: "assistant", content: "Hi there! How can I help?", sources: [], confidence_score: 0.9, created_at: new Date().toISOString() },
    ])
  }),

  http.get(`${API}/admin/metrics`, () => {
    return HttpResponse.json({
      total_documents: 42,
      total_users: 10,
      total_chat_sessions: 5,
      documents_by_status: { ready: 30, pending: 5, processing: 5, failed: 2 },
      total_tokens_used: 123456,
      avg_chat_latency_ms: 234,
      avg_search_latency_ms: 45,
      error_count: 1,
    })
  }),

  http.get(`${API}/admin/audit`, () => {
    return HttpResponse.json({
      items: [
        { id: 1, user_email: "admin@eka.com", action: "login", resource: "auth", details: null, ip_address: "127.0.0.1", success: 1, created_at: new Date().toISOString() },
      ],
      total: 1,
      skip: 0,
      limit: 200,
    })
  }),

  http.get("*/health", () => {
    return HttpResponse.json({ status: "healthy", service: "Enterprise Knowledge Assistant", version: "1.0.0" })
  }),
]
