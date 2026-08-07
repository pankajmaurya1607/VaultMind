import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import api from "../lib/api"
import type { SearchResponse } from "../types"

export function useSearch() {
  const [query, setQuery] = useState("")
  const [enabled, setEnabled] = useState(false)

  const search = useQuery<SearchResponse>({
    queryKey: ["search", query],
    queryFn: async () => {
      const { data } = await api.post("/search", { query, top_k: 10 })
      return data
    },
    enabled,
  })

  const run = (q: string) => {
    setQuery(q)
    setEnabled(true)
  }

  return { query, setQuery, run, ...search }
}
