import { useQuery } from "@tanstack/react-query"
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
