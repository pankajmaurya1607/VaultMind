import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "../lib/api"
import type { ChatSession, ChatResponse, Message } from "../types"

export function useChatSessions() {
  return useQuery<ChatSession[]>({
    queryKey: ["chat-sessions"],
    queryFn: async () => {
      const { data } = await api.get("/chat/history")
      return data
    },
  })
}

export function useChatMessages(sessionId: number | null) {
  return useQuery<Message[]>({
    queryKey: ["chat-messages", sessionId],
    queryFn: async () => {
      const { data } = await api.get(`/chat/history/${sessionId}`)
      return data
    },
    enabled: !!sessionId,
  })
}

export function useSendMessage() {
  const qc = useQueryClient()
  return useMutation<ChatResponse, Error, { sessionId: number | null; question: string }>({
    mutationFn: async ({ sessionId, question }) => {
      const { data } = await api.post("/chat", {
        session_id: sessionId,
        question,
      })
      return data
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["chat-sessions"] })
      qc.invalidateQueries({ queryKey: ["chat-messages", data.session_id] })
    },
  })
}
