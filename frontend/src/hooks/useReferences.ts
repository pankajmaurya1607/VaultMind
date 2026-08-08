import { useQuery } from "@tanstack/react-query"
import api from "../lib/api"
import type { Label } from "../types"

export function useDepartments() {
  return useQuery<Label[]>({
    queryKey: ["departments"],
    queryFn: async () => {
      const { data } = await api.get("/departments")
      return data
    },
  })
}

export function useRoles() {
  return useQuery<Label[]>({
    queryKey: ["roles"],
    queryFn: async () => {
      const { data } = await api.get("/departments/roles")
      return data
    },
  })
}