import { useQuery } from "@tanstack/react-query"
import api, { API_ORIGIN } from "@/lib/api"

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => {
      // /health lives at the backend root, not under /api/v1.
      const { data } = await api.get("/health", { baseURL: API_ORIGIN })
      return data
    },
    retry: 1,
    refetchInterval: 30_000,
  })
}
