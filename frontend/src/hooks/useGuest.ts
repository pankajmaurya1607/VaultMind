import { useState, useEffect } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import api, { API_ORIGIN } from "@/lib/api"

const GUEST_TOKEN_KEY = "vaultmind_guest_token"

export function getGuestToken(): string | null {
  return localStorage.getItem(GUEST_TOKEN_KEY)
}

export function setGuestToken(token: string) {
  localStorage.setItem(GUEST_TOKEN_KEY, token)
}

export function clearGuestToken() {
  localStorage.removeItem(GUEST_TOKEN_KEY)
}

export interface GuestStatus {
  guest_token: string
  documents: Array<{
    id: number
    filename: string
    status: string
    chunk_count: number
    error_message: string | null
    expires_at: string
    created_at: string
  }>
  expires_in_seconds: number
  ttl_minutes: number
}

export function useGuestStatus() {
  const token = getGuestToken()
  return useQuery<GuestStatus>({
    queryKey: ["guest", "status", token],
    queryFn: async () => {
      const { data } = await api.get("/guest/status", {
        headers: token ? { "X-Guest-Token": token } : {},
        params: token ? { guest_token: token } : {},
      })
      return data
    },
    enabled: !!token,
    refetchInterval: (query) => {
      const data = query.state.data as GuestStatus | undefined
      const hasPending = data?.documents?.some((d) => d.status === "pending" || d.status === "processing")
      return hasPending ? 3000 : 10000
    },
  })
}

export function useGuestUpload() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const token = getGuestToken()
      const form = new FormData()
      form.append("file", file)
      const { data } = await api.post("/guest/upload", form, {
        headers: {
          "Content-Type": "multipart/form-data",
          ...(token ? { "X-Guest-Token": token } : {}),
        },
      })
      if (data.guest_token) setGuestToken(data.guest_token)
      return data as { id: number; guest_token: string; filename: string; status: string; expires_at: string; ttl_minutes: number; message: string }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["guest", "status"] }),
  })
}

export function useGuestChat() {
  return useMutation({
    mutationFn: async (question: string) => {
      const token = getGuestToken()
      if (!token) throw new Error("No guest session. Upload a file first.")
      const { data } = await api.post(
        "/guest/chat",
        { question, guest_token: token },
        { headers: token ? { "X-Guest-Token": token } : {} }
      )
      return data as { answer: string; sources: Array<{ document_id: number; filename: string; chunk_index: number; text: string; score: number }>; confidence_score: number; tokens_used: number; latency_ms: number; model: string; model_provider: string }
    },
  })
}

export function useGuestClear() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const token = getGuestToken()
      const { data } = await api.delete("/guest/clear", {
        headers: token ? { "X-Guest-Token": token } : {},
        params: token ? { guest_token: token } : {},
      })
      clearGuestToken()
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["guest"] }),
  })
}

export function useGuestTTL(expiresAt?: string, expiresInSeconds?: number) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!expiresAt && expiresInSeconds == null) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [expiresAt, expiresInSeconds])
  if (expiresInSeconds != null) {
    return Math.max(0, expiresInSeconds - Math.floor((Date.now() - now) / 1000))
  }
  if (!expiresAt) return 0
  const end = new Date(expiresAt).getTime()
  return Math.max(0, Math.floor((end - Date.now()) / 1000))
}

// Re-export API origin for direct links if needed
export { API_ORIGIN }
