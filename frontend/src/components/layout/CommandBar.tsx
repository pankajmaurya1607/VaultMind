import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { Search, Files, MessageSquare, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"

export default function CommandBar() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
      if (e.key === "Escape") setOpen(false)
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [])

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100)
    } else {
      setQuery("")
    }
  }, [open])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = query.trim()
    if (trimmed) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`)
    } else {
      navigate("/search")
    }
    setOpen(false)
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex w-full max-w-xl items-center gap-2 rounded-lg border bg-card px-3 py-2 text-sm text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
        aria-label="Open search"
      >
        <Search className="h-4 w-4 shrink-0" />
        <span className="flex-1 text-left">Search knowledge base...</span>
        <kbd className="hidden sm:inline-flex items-center gap-1 rounded border bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
          ⌘K
        </kbd>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-lg" aria-describedby={undefined}>
          <DialogHeader className="sr-only">
            <DialogTitle>Search</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="flex items-center gap-3 border-b px-4 py-3">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search documents or ask a question..."
              className="flex-1 border-0 shadow-none focus-visible:ring-0 px-0 h-7"
            />
            <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(false)} className="h-7 px-2">
              <X className="h-3.5 w-3.5" />
              ESC
            </Button>
          </form>
          <div className="px-4 py-3">
            {query.trim() ? (
              <p className="text-sm text-muted-foreground">
                Press <span className="font-medium text-primary">Enter</span> to search for &quot;{query.trim()}&quot;
              </p>
            ) : (
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Quick links</p>
                <button
                  onClick={() => {
                    navigate("/documents")
                    setOpen(false)
                  }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors text-left"
                >
                  <Files className="h-4 w-4" /> Browse Documents
                </button>
                <button
                  onClick={() => {
                    navigate("/chat")
                    setOpen(false)
                  }}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors text-left"
                >
                  <MessageSquare className="h-4 w-4" /> Open Chat
                </button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
