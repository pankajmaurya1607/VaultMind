import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "../lib/api"
import type { User, AuditLog, SystemMetrics } from "../types"

export function useAdminUsers(pagination?: { skip: number; limit: number }) {
  const skip = pagination?.skip ?? 0
  const limit = pagination?.limit ?? 100
  return useQuery<User[]>({
    queryKey: ["admin", "users", skip, limit],
    queryFn: async () => {
      const { data } = await api.get(`/users?skip=${skip}&limit=${limit}`)
      return data
    },
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, name, role_id, department_id }: { id: number; name?: string; role_id?: number; department_id?: number | null }) => {
      const { data } = await api.patch(`/users/${id}`, {
        name,
        role_id,
        department_id,
      })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "users"] }),
  })
}

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: { name: string; email: string; password: string; department_id: number; role_id?: number }) => {
      const { data } = await api.post("/auth/register", body)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "users"] }),
  })
}

export function useAdminAuditLogs(limit = 200) {
  return useQuery<AuditLog[]>({
    queryKey: ["admin", "audit", limit],
    queryFn: async () => {
      const { data } = await api.get(`/admin/audit?limit=${limit}`)
      return data
    },
  })
}

export function useAdminMetrics() {
  return useQuery<SystemMetrics>({
    queryKey: ["admin", "metrics"],
    queryFn: async () => {
      const { data } = await api.get("/admin/metrics")
      return data
    },
  })
}
