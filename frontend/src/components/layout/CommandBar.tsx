import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"

export default function CommandBar() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
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
      setTimeout(() => inputRef.current?.focus(), 50)
    } else {
      setQuery("")
    }
  }, [open])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = query.trim()
    if (trimmed) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`)
      setOpen(false)
    } else {
      navigate("/search")
      setOpen(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 w-full max-w-xl mx-auto bg-bg-surface border border-border hover:border-accent/30 rounded-xl px-4 py-2.5 text-sm text-text-muted transition-colors group"
      >
        <span className="text-text-dim group-hover:text-text-muted transition-colors">🔍</span>
        <span className="flex-1 text-left">Search knowledge base...</span>
        <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 bg-bg-base border border-border rounded-md text-xs text-text-dim font-mono">
          <span>⌘</span>K
        </kbd>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm animate-fade-in"
          onClick={(e) => {
            if (e.target === e.currentTarget) setOpen(false)
          }}
        >
          <div className="w-full max-w-lg bg-bg-elevated border border-border rounded-xl shadow-2xl overflow-hidden animate-fade-in">
            <form onSubmit={handleSubmit} className="flex items-center gap-3 px-4 py-3 border-b border-border">
              <span className="text-text-muted text-lg">🔍</span>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search documents or ask a question..."
                className="flex-1 bg-transparent text-text placeholder:text-text-dim text-sm focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="text-text-dim hover:text-text text-xs bg-bg-surface px-2 py-1 rounded"
              >
                ESC
              </button>
            </form>
            <div className="px-4 py-3">
              {query.trim() ? (
                <p className="text-sm text-text-muted">
                  Press <span className="text-accent">Enter</span> to search for "{query.trim()}"
                </p>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs text-text-dim uppercase tracking-wider font-medium">Quick links</p>
                  <button
                    onClick={() => { navigate("/documents"); setOpen(false) }}
                    className="block w-full text-left px-3 py-2 rounded-lg text-sm text-text-muted hover:text-text hover:bg-bg-hover transition-colors"
                  >
                    ◇ Browse Documents
                  </button>
                  <button
                    onClick={() => { navigate("/chat"); setOpen(false) }}
                    className="block w-full text-left px-3 py-2 rounded-lg text-sm text-text-muted hover:text-text hover:bg-bg-hover transition-colors"
                  >
                    ◉ Open Chat
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
