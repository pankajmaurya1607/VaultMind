import { useState, useRef, useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { useSearch } from "../hooks/useSearch"

function scoreColor(score: number) {
  if (score >= 0.9) return "text-accent"
  if (score >= 0.8) return "text-blue-400"
  return "text-text-muted"
}

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const initialQ = searchParams.get("q") || ""
  const [input, setInput] = useState(initialQ)
  const { query, run, data, isLoading, error, isFetching } = useSearch()
  const inputRef = useRef<HTMLInputElement>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  useEffect(() => {
    if (initialQ) run(initialQ)
  }, [run, initialQ])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) run(input.trim())
  }

  const toggleExpand = (index: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  const fuzzyMatch = (text: string, q: string) => {
    if (!q) return text
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    const parts = text.split(new RegExp(`(${escaped})`, "gi"))
    return parts.map((part, i) =>
      part.toLowerCase() === q.toLowerCase()
        ? <mark key={i} className="bg-accent/20 text-accent rounded-sm px-0.5">{part}</mark>
        : part
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto animate-fade-in">
      <h1 className="text-xl font-semibold text-text mb-5">Search</h1>

      <form onSubmit={handleSubmit} className="flex gap-3 mb-6">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search your knowledge base..."
          className="flex-1 bg-bg-surface border border-border rounded-lg px-4 py-2.5 text-text placeholder:text-text-dim text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
        />
        <button
          type="submit"
          disabled={isFetching || !input.trim()}
          className="px-5 py-2.5 text-sm font-medium text-white bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          {isFetching ? "Searching..." : "Search"}
        </button>
      </form>

      {isLoading && (
        <div className="text-sm text-text-muted py-12 text-center">Searching...</div>
      )}

      {error && (
        <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-3">
          Search failed. Please try again.
        </div>
      )}

      {data && data.total === 0 && (
        <div className="text-sm text-text-muted py-12 text-center">
          No results found for "{query}".
        </div>
      )}

      {data && data.total > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-text-dim mb-3">
            {data.total} result{data.total !== 1 ? "s" : ""} for "{query}"
          </p>
          {data.results.map((r, i) => {
            const isExpanded = expanded.has(i) || r.text.length < 300
            return (
              <div
                key={`${r.document_id}-${r.chunk_index}`}
                className="bg-bg-surface border border-border rounded-xl p-4 hover:border-accent/20 transition-colors cursor-pointer"
                onClick={() => toggleExpand(i)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-sm font-medium text-text truncate">
                      {r.filename}
                    </span>
                    <span className="text-xs text-text-dim whitespace-nowrap">
                      Chunk {r.chunk_index}
                    </span>
                  </div>
                  <span className={`text-xs font-mono font-medium whitespace-nowrap ml-3 ${scoreColor(r.score)}`}>
                    {(r.score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-sm text-text-muted leading-relaxed">
                  {isExpanded ? fuzzyMatch(r.text, query) : fuzzyMatch(r.text.slice(0, 200) + "...", query)}
                </p>
                {!isExpanded && (
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleExpand(i) }}
                    className="text-xs text-accent hover:text-accent-hover mt-1"
                  >
                    Show more
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
