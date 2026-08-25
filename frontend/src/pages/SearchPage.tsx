import { useState, useRef, useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { useSearch } from "@/hooks/useSearch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search as SearchIcon, Loader2, FileText, ChevronDown, ChevronUp, Settings2 } from "lucide-react"
import { cn } from "@/lib/utils"

function scoreVariant(score: number): "default" | "secondary" | "outline" {
  if (score >= 0.9) return "default"
  if (score >= 0.8) return "secondary"
  return "outline"
}

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const initialQ = searchParams.get("q") || ""
  const [input, setInput] = useState(initialQ)
  const { query, topK, setTopK, run, data, isLoading, error, isFetching } = useSearch()
  const inputRef = useRef<HTMLInputElement>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  useEffect(() => {
    if (initialQ) run(initialQ)
  }, [run, initialQ])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) run(input.trim(), topK)
  }

  const handleTopKChange = (v: string) => {
    const k = Number(v)
    setTopK(k)
    if (query) run(query, k)
    else if (input.trim()) run(input.trim(), k)
  }

  const toggleExpand = (index: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  const highlight = (text: string, q: string) => {
    if (!q) return text
    const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    const parts = text.split(new RegExp(`(${escaped})`, "gi"))
    return parts.map((part, i) =>
      part.toLowerCase() === q.toLowerCase() ? (
        <mark key={i} className="bg-primary/15 text-primary rounded-sm px-0.5">
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  const isRateLimited = (error as { response?: { status?: number } })?.response?.status === 429

  return (
    <div className="mx-auto max-w-4xl p-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Search</h1>
        <p className="text-sm text-muted-foreground mt-1">Semantic search across your knowledge base</p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Search your knowledge base... e.g. onboarding, Q4 report"
            className="pl-9"
          />
        </div>
        <div className="flex gap-2">
          <Select value={String(topK)} onValueChange={handleTopKChange}>
            <SelectTrigger className="w-[110px]" aria-label="Results per search">
              <Settings2 className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="5">Top 5</SelectItem>
              <SelectItem value="10">Top 10</SelectItem>
              <SelectItem value="20">Top 20</SelectItem>
            </SelectContent>
          </Select>
          <Button type="submit" disabled={isFetching || !input.trim()} className="gap-2 min-w-[96px]">
            {isFetching ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Searching...
              </>
            ) : (
              <>
                <SearchIcon className="h-4 w-4" /> Search
              </>
            )}
          </Button>
        </div>
      </form>
      <p className="text-xs text-muted-foreground mt-2">Top-K retrieval: {topK} · Cosine similarity ≥ 0.7 · Department-filtered</p>

      <div className="mt-6">
        {isLoading && (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        )}

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {isRateLimited ? "Rate limited (60/min). Please wait a moment and try again." : "Search failed. Please try again."}
          </div>
        )}

        {data && data.total === 0 && !isFetching && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <div className="rounded-full bg-muted p-3 mb-3">
                <SearchIcon className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium">No results found for &quot;{query}&quot;.</p>
              <p className="text-xs text-muted-foreground mt-1">Try rephrasing or using different keywords.</p>
            </CardContent>
          </Card>
        )}

        {data && data.total > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                {data.total} result{data.total !== 1 ? "s" : ""} for &quot;<span className="font-medium text-foreground">{query}</span>&quot; · Top {topK}
                {isFetching && <span className="ml-2 inline-flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> refreshing...</span>}
              </p>
            </div>

            {data.results.map((r, i) => {
              const isExpanded = expanded.has(i) || r.text.length < 300
              return (
                <Card
                  key={`${r.document_id}-${r.chunk_index}`}
                  className="cursor-pointer transition-colors hover:border-primary/20"
                  role="button"
                  tabIndex={0}
                  aria-expanded={isExpanded}
                  onClick={() => toggleExpand(i)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault()
                      toggleExpand(i)
                    }
                  }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className="rounded-md bg-primary/10 p-1.5">
                          <FileText className="h-3.5 w-3.5 text-primary" />
                        </div>
                        <span className="truncate text-sm font-medium">{r.filename}</span>
                        <span className="hidden sm:inline text-xs text-muted-foreground whitespace-nowrap">Chunk {r.chunk_index}</span>
                      </div>
                      <Badge variant={scoreVariant(r.score)} className="shrink-0 font-mono text-xs">
                        {(r.score * 100).toFixed(0)}%
                      </Badge>
                    </div>

                    <p className={cn("text-sm leading-relaxed text-muted-foreground", !isExpanded && "line-clamp-2")}>
                      {isExpanded ? highlight(r.text, query) : highlight(r.text.slice(0, 220) + (r.text.length > 220 ? "..." : ""), query)}
                    </p>

                    {r.metadata && Object.keys(r.metadata).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {Object.entries(r.metadata).slice(0, 4).map(([k, v]) => (
                          <Badge key={k} variant="outline" className="text-[10px] px-1.5 py-0">
                            {k}: {String(v).slice(0, 30)}
                          </Badge>
                        ))}
                      </div>
                    )}

                    <div className="mt-2 flex items-center">
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
                        {isExpanded ? (
                          <>
                            Show less <ChevronUp className="h-3 w-3" />
                          </>
                        ) : r.text.length > 220 ? (
                          <>
                            Show more <ChevronDown className="h-3 w-3" />
                          </>
                        ) : null}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}

        {!data && !isLoading && !error && (
          <Card className="border-dashed mt-6">
            <CardContent className="py-10 text-center">
              <SearchIcon className="mx-auto h-8 w-8 text-muted-foreground/40 mb-3" />
              <p className="text-sm text-muted-foreground">Enter a query to search your documents.</p>
              <p className="text-xs text-muted-foreground/70 mt-1">Try &quot;company policies&quot; or &quot;how to deploy&quot;</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
