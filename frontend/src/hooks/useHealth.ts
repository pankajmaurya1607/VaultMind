import { useQuery } from "@tanstack/react-query"
import api from "@/lib/api"

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => {
      const { data } = await api.get("/health", { baseURL: "http://localhost:8000" })
      return data
    },
    retry: 1,
    refetchInterval: 30_000,
  })
}
