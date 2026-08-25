import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "../lib/api"
import type { Document, DocumentUploadResponse, Paginated } from "../types"

export function useDocuments(refetchMs?: number, pagination?: { skip: number; limit: number }) {
  const skip = pagination?.skip ?? 0
  const limit = pagination?.limit ?? 100
  return useQuery<Paginated<Document>>({
    queryKey: ["documents", skip, limit],
    queryFn: async () => {
      const { data } = await api.get(`/documents?skip=${skip}&limit=${limit}`)
      return data
    },
    refetchInterval: (query) => {
      if (refetchMs == null) return false
      const docs = query.state.data?.items
      const pending = docs?.some((d) => d.status === "pending" || d.status === "processing")
      return pending ? refetchMs : false
    },
  })
}

export function useDocument(id: number | null) {
  return useQuery<Document>({
    queryKey: ["documents", id],
    queryFn: async () => {
      const { data } = await api.get(`/documents/${id}`)
      return data
    },
    enabled: id != null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === "pending" || status === "processing" ? 5000 : false
    },
  })
}

export function useUploadDocument() {
  const qc = useQueryClient()
  return useMutation<DocumentUploadResponse, Error, File>({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append("file", file)
      const { data } = await api.post("/documents", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  })
}

export function useDeleteDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/documents/${id}`)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  })
}