import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import api from "../lib/api"
import type { User, AuditLog, SystemMetrics } from "../types"

export function useAdminUsers() {
  return useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const { data } = await api.get("/users")
      return data
    },
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, role_id, department_id }: { id: number; role_id?: number; department_id?: number | null }) => {
      const { data } = await api.patch(`/users/${id}`, {
        role_id,
        department_id,
      })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "users"] }),
  })
}

export function useAdminAuditLogs() {
  return useQuery<AuditLog[]>({
    queryKey: ["admin", "audit"],
    queryFn: async () => {
      const { data } = await api.get("/admin/audit?limit=200")
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
