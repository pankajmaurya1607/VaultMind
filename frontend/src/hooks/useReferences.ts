import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
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

export function useCreateDepartment() {
  const qc = useQueryClient()
  return useMutation<Label, Error, string>({
    mutationFn: async (name: string) => {
      const { data } = await api.post("/admin/departments", { name })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["departments"] }),
  })
}

export function useCreateRole() {
  const qc = useQueryClient()
  return useMutation<Label, Error, string>({
    mutationFn: async (name: string) => {
      const { data } = await api.post("/admin/roles", { name })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  })
}