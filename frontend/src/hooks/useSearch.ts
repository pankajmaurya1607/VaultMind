import { useState, useCallback } from "react"
import { useQuery } from "@tanstack/react-query"
import api from "../lib/api"
import type { SearchResponse } from "../types"

export function useSearch() {
  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState(5)
  const [enabled, setEnabled] = useState(false)

  const search = useQuery<SearchResponse>({
    queryKey: ["search", query, topK],
    queryFn: async () => {
      const { data } = await api.post("/search", { query, top_k: topK })
      return data
    },
    enabled,
  })

  const run = useCallback((q: string, k?: number) => {
    setQuery(q)
    if (k !== undefined) setTopK(k)
    setEnabled(true)
  }, [])

  return { query, topK, setTopK, setQuery, run, ...search }
}
