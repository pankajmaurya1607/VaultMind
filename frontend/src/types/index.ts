export interface User {
  id: number
  name: string
  email: string
  department_id: number
  department_name: string
  role_id: number
  role_name: string
  created_at: string
}

export interface Document {
  id: number
  original_filename: string
  file_size: number
  mime_type: string
  status: "pending" | "processing" | "ready" | "failed"
  uploaded_by: number
  department_id: number
  chunk_count: number
  error_message: string | null
  created_at: string
}

export interface Chunk {
  document_id: number
  filename: string
  chunk_index: number
  text: string
  score: number
  metadata: Record<string, unknown>
}

export interface ChatSession {
  id: number
  title: string
  created_at: string
  message_count?: number
}

export interface Message {
  id: number
  role: "user" | "assistant"
  content: string
  sources: Chunk[] | null
  confidence_score: number | null
  created_at: string
}

export interface ChatResponse {
  session_id: number
  answer: string
  sources: Chunk[]
  confidence_score: number
  tokens_used: number
  latency_ms: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface SystemMetrics {
  total_documents: number
  total_users: number
  total_chat_sessions: number
  documents_by_status: Record<string, number>
  total_tokens_used: number
  avg_chat_latency_ms: number
  avg_search_latency_ms: number
  error_count: number
}

export interface AuditLog {
  id: number
  user_email: string | null
  action: string
  resource: string
  details: string | null
  ip_address: string | null
  success: number
  created_at: string
}

export interface RegisterBody {
  name: string
  email: string
  password: string
  department_id: number
  role_id?: number
}

export interface LoginBody {
  email: string
  password: string
}

export interface SearchBody {
  query: string
  top_k?: number
}

export interface SearchResponse {
  results: Chunk[]
  total: number
}

export interface ChatBody {
  session_id: number | null
  question: string
}

export interface Department {
  id: number
  name: string
}
