import { useState, useEffect, useRef } from "react"
import { Link } from "react-router-dom"
import { useGuestStatus, useGuestUpload, useGuestChat, useGuestClear, getGuestToken, clearGuestToken } from "@/hooks/useGuest"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { toast } from "sonner"
import { Upload, Send, Loader2, Trash2, Clock, Sparkles, FileText, Shield, Timer, ChevronDown, ChevronUp, Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"

function formatTTL(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, "0")}`
}

function formatAnswer(text: string) {
  // Clean up PDF artifacts and render markdown-ish
  const cleaned = text
    .replace(/【([^】]+)】/g, "[$1]") // normalize 【file】 -> [file]
    .replace(/\u3010/g, "[")
    .replace(/\u3011/g, "]")
  const parts = cleaned.split("\n")
  return parts.map((line, idx) => {
    const trimmed = line.trim()
    if (!trimmed) return <div key={idx} className="h-2" />
    // Heading detection (e.g., **Title** on its own line)
    const isHeading = /^\*\*.+\*\*$/.test(trimmed) && trimmed.length < 80
    let html = line
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\[(\d+)\]/g, '<span class="inline-flex items-center justify-center rounded bg-primary/10 text-primary text-[10px] px-1.5 py-0 ml-1">$1</span>')
      .replace(/\[([^\]]+\.(pdf|docx|txt|md|csv|xlsx))\]/gi, '<span class="inline-flex items-center gap-1 rounded bg-primary/10 text-primary text-[11px] px-1.5 py-0 ml-1">📄 $1</span>')
    // Bullet/numbered list styling
    const isList = /^(\d+\.|\-|\•)\s/.test(trimmed)
    if (isHeading) {
      return <p key={idx} className="text-sm font-semibold mt-3 mb-1" dangerouslySetInnerHTML={{ __html: html }} />
    }
    if (isList) {
      return <p key={idx} className="text-sm leading-relaxed ml-4 flex gap-2"><span className="text-primary">•</span><span dangerouslySetInnerHTML={{ __html: html.replace(/^(\d+\.|\-|\•)\s/, "") }} /></p>
    }
    return <p key={idx} className="text-sm leading-relaxed" dangerouslySetInnerHTML={{ __html: html }} />
  })
}

function GuestSourceBlock({ sources }: { sources: Array<{ filename: string; chunk_index: number; text: string; score: number }> }) {
  const [open, setOpen] = useState(false)
  if (!sources || sources.length === 0) return null
  const hasScores = sources.some((s) => s.score > 0.01)
  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-3">
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1">
          {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {open ? "Hide" : "Show"} sources ({sources.length})
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-1.5">
        {sources.map((s, i) => (
          <div key={i} className="rounded-md border bg-muted/50 px-3 py-2 text-xs">
            <div className="flex items-center gap-2">
              <FileText className="h-3 w-3 text-muted-foreground" />
              <span className="font-medium truncate">{s.filename}</span>
              <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">chunk {s.chunk_index}</Badge>
              {hasScores && <span className="ml-auto font-mono text-[11px] text-muted-foreground">{(s.score * 100).toFixed(0)}%</span>}
            </div>
            <p className="mt-1.5 text-muted-foreground leading-relaxed line-clamp-3">{s.text.slice(0, 200)}</p>
          </div>
        ))}
      </CollapsibleContent>
    </Collapsible>
  )
}

type GuestHistoryItem = {
  id: number
  role: "user" | "assistant"
  content: string
  sources?: Array<{ filename: string; chunk_index: number; text: string; score: number }>
  model?: string
  latency_ms?: number
  confidence?: number
}

export default function QuickTryPage() {
  const { data: status, isLoading: statusLoading, refetch } = useGuestStatus()
  const upload = useGuestUpload()
  const chat = useGuestChat()
  const clear = useGuestClear()
  const [question, setQuestion] = useState("")
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const [nowTick, setNowTick] = useState(Date.now())
  const [history, setHistory] = useState<GuestHistoryItem[]>(() => {
    try {
      const raw = localStorage.getItem("vaultmind_guest_history")
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  })
  const bottomRef = useRef<HTMLDivElement>(null)

  const doc = status?.documents?.[0]
  const expiresIn = (() => {
    if (!doc?.expires_at) return status?.expires_in_seconds ?? 0
    const end = new Date(doc.expires_at).getTime()
    return Math.max(0, Math.floor((end - nowTick) / 1000))
  })()

  useEffect(() => {
    if (!doc) return
    const id = setInterval(() => setNowTick(Date.now()), 1000)
    return () => clearInterval(id)
  }, [doc?.expires_at])

  // auto-refetch when processing
  useEffect(() => {
    if (doc?.status === "pending" || doc?.status === "processing") {
      const id = setInterval(() => refetch(), 3000)
      return () => clearInterval(id)
    }
  }, [doc?.status, refetch])

  // persist history per guest_token
  useEffect(() => {
    const token = getGuestToken()
    if (token && history.length > 0) {
      localStorage.setItem("vaultmind_guest_history", JSON.stringify(history.slice(-20)))
    }
  }, [history])

  // clear history when token changes or doc expires
  useEffect(() => {
    if (!doc && history.length > 0 && !getGuestToken()) {
      setHistory([])
      localStorage.removeItem("vaultmind_guest_history")
    }
  }, [doc, history.length])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [history, chat.isPending])

  const handleFile = async (file: File) => {
    if (file.size > 1 * 1024 * 1024) {
      toast.error("Quick Try limit is 1MB. Sign up for 10MB files.")
      return
    }
    try {
      await upload.mutateAsync(file)
      toast.success("File uploaded - processing...")
      refetch()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || (err as Error).message || "Upload failed"
      toast.error(msg)
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const onAsk = async () => {
    const q = question.trim()
    if (!q || chat.isPending) return
    if (!doc || doc.status !== "ready") {
      toast.error(doc?.status === "processing" || doc?.status === "pending" ? "File still processing, wait a few seconds" : "Upload a file first")
      return
    }
    const userMsg: GuestHistoryItem = { id: Date.now(), role: "user", content: q }
    setHistory((h) => [...h, userMsg])
    setQuestion("")
    try {
      const res = await chat.mutateAsync(q)
      const assistantMsg: GuestHistoryItem = {
        id: Date.now() + 1,
        role: "assistant",
        content: res.answer,
        sources: res.sources,
        model: res.model,
        latency_ms: res.latency_ms,
        confidence: res.confidence_score,
      }
      setHistory((h) => [...h, assistantMsg])
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || (err as Error).message
      toast.error(msg || "Chat failed")
      setQuestion(q)
      // remove optimistic user message on failure
      setHistory((h) => h.filter((m) => m.id !== userMsg.id))
    }
  }

  const handleClear = async () => {
    try {
      await clear.mutateAsync()
      chat.reset()
      setHistory([])
      localStorage.removeItem("vaultmind_guest_history")
      toast.success("Session cleared")
    } catch {
      clearGuestToken()
      setHistory([])
      localStorage.removeItem("vaultmind_guest_history")
      toast.success("Session cleared")
    }
  }

  const hasToken = !!getGuestToken()

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2 text-lg font-semibold">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground"><Sparkles className="h-4 w-4" /></div>
            VaultMind <Badge variant="secondary" className="ml-2 text-xs">Quick Try</Badge>
          </Link>
          <div className="flex items-center gap-2">
            {doc && (
              <Badge variant={expiresIn < 120 ? "destructive" : "secondary"} className="gap-1 font-mono">
                <Timer className="h-3 w-3" /> {formatTTL(expiresIn)} left
              </Badge>
            )}
            <Button variant="ghost" asChild><Link to="/login">Log in</Link></Button>
            <Button asChild><Link to="/register">Sign up</Link></Button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-8">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-semibold tracking-tight">Try VaultMind instantly</h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-2xl mx-auto">
            Upload a file <strong>&lt;1MB</strong> (PDF, DOCX, TXT, MD, CSV, XLSX) and chat with it immediately. No signup. Auto-deletes in <strong>10 minutes</strong>.
          </p>
          <div className="mt-3 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <Shield className="h-3.5 w-3.5" /> No account needed · <Clock className="h-3.5 w-3.5" /> TTL 10 min · <FileText className="h-3.5 w-3.5" /> 1 file per session
          </div>
        </div>

        <div className="grid lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2"><Upload className="h-4 w-4" /> Upload</CardTitle>
                <CardDescription>1 file, max 1MB. Same parsing as full app.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={onDrop}
                  onClick={() => fileRef.current?.click()}
                  className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/20 hover:border-primary/30"}`}
                >
                  <div className="rounded-full bg-primary/10 p-3 mb-3"><Upload className="h-5 w-5 text-primary" /></div>
                  <p className="text-sm font-medium">Drop file or click to browse</p>
                  <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, TXT, MD, CSV, XLSX · &lt;1MB</p>
                  <input ref={fileRef} type="file" className="hidden" accept=".pdf,.docx,.txt,.md,.csv,.xlsx" onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); e.target.value = "" }} />
                </div>

                {upload.isPending && <p className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Uploading...</p>}

                {statusLoading && hasToken && <p className="text-xs text-muted-foreground">Checking session...</p>}

                {doc && (
                  <div className="rounded-lg border p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium truncate pr-2 flex items-center gap-2"><FileText className="h-4 w-4 text-muted-foreground" />{doc.filename}</span>
                      <Badge variant={doc.status === "ready" ? "default" : doc.status === "failed" ? "destructive" : "secondary"} className="capitalize text-xs">{doc.status}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{doc.chunk_count} chunks</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{formatTTL(expiresIn)}</span>
                    </div>
                    {(doc.status === "pending" || doc.status === "processing") && <p className="flex items-center gap-1 text-xs text-primary"><Loader2 className="h-3 w-3 animate-spin" />Processing... chat unlocks when ready</p>}
                    {doc.error_message && <p className="text-xs text-destructive bg-destructive/10 border border-destructive/20 rounded p-2">{doc.error_message}</p>}
                  </div>
                )}

                {doc && (
                  <Button variant="outline" size="sm" onClick={handleClear} disabled={clear.isPending} className="w-full gap-2"><Trash2 className="h-3.5 w-3.5" /> Clear session</Button>
                )}

                <p className="text-xs text-muted-foreground text-center">Want 10MB, multiple files & history? <Link to="/register" className="text-primary hover:underline font-medium">Create account</Link></p>
              </CardContent>
            </Card>

            <Card className="bg-muted/30">
              <CardContent className="pt-6 text-xs text-muted-foreground leading-relaxed">
                <strong>How it works:</strong> File is stored under <code className="bg-background px-1 py-0.5 rounded">guest/{getGuestToken()?.slice(0,8) ?? "—"}</code>, chunked → embedded (384-dim BGE) → PGVector, isolated to your <code>guest_token</code>. Auto-deleted after 10 min via TTL sweeper (`app/services/guest.py: cleanup_expired`) and background `cleanup_expired_guest_documents` task.
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-3">
            <Card className="h-[560px] flex flex-col">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2"><Sparkles className="h-4 w-4 text-primary" /> Chat with your file</CardTitle>
                <CardDescription>Answers are cited from your upload only. Same RAG pipeline as logged-in users.</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
                <ScrollArea className="flex-1">
                  <div className="p-4 space-y-4">
                    {!doc && (
                      <div className="flex flex-col items-center justify-center py-16 text-center">
                        <div className="rounded-full bg-primary/10 p-4 mb-3"><FileText className="h-6 w-6 text-primary" /></div>
                        <p className="text-sm font-medium">No file yet</p>
                        <p className="text-xs text-muted-foreground mt-1 max-w-sm">Upload a PDF or DOCX (&lt;1MB) to start chatting. You’ll get the same AI search & citations as full users.</p>
                      </div>
                    )}
                    {doc && doc.status !== "ready" && (
                      <div className="flex flex-col items-center justify-center py-12 text-center">
                        <Loader2 className="h-6 w-6 animate-spin text-primary mb-3" />
                        <p className="text-sm">Processing <strong>{doc.filename}</strong>...</p>
                        <p className="text-xs text-muted-foreground mt-1">Chunking & embedding — usually 3-5 seconds</p>
                      </div>
                    )}
                    {doc?.status === "ready" && history.length === 0 && !chat.isPending && (
                      <div className="text-center py-8">
                        <p className="text-sm font-medium">Ready! Ask anything about <strong>{doc.filename}</strong></p>
                        <div className="mt-4 grid gap-2 text-left max-w-md mx-auto">
                          {["Summarize this document", "What are the key points?", "Extract action items"].map((q) => (
                            <button key={q} onClick={() => setQuestion(q)} className="rounded-lg border p-3 text-left text-sm hover:bg-accent transition-colors">
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                    {history.map((m) => (
                      <div key={m.id} className={cn("flex gap-2", m.role === "user" ? "justify-end" : "justify-start")}>
                        {m.role === "assistant" && (
                          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                            <Bot className="h-3.5 w-3.5" />
                          </div>
                        )}
                        <div className={cn("max-w-[80%] rounded-2xl px-4 py-3 text-sm", m.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border shadow-sm")}>
                          {m.role === "assistant" ? <div className="space-y-1">{formatAnswer(m.content)}</div> : <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>}
                          {m.role === "assistant" && m.sources && m.sources.length > 0 && <GuestSourceBlock sources={m.sources} />}
                          {m.role === "assistant" && (
                            <p className="mt-2 text-xs opacity-60">
                              {m.confidence != null && m.confidence > 0.05 ? `Relevance ${(m.confidence * 100).toFixed(0)}% · ` : ""}
                              {m.latency_ms != null ? `${m.latency_ms}ms · ` : ""}
                              {m.model ?? "template"} · ttl {formatTTL(expiresIn)}
                            </p>
                          )}
                        </div>
                        {m.role === "user" && (
                          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary">
                            <User className="h-3.5 w-3.5" />
                          </div>
                        )}
                      </div>
                    ))}
                    {chat.isPending && (
                      <div className="flex gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground shrink-0"><Bot className="h-3.5 w-3.5" /></div>
                        <div className="rounded-2xl border bg-card px-4 py-3 text-sm text-muted-foreground flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Thinking...</div>
                      </div>
                    )}
                    <div ref={bottomRef} />
                  </div>
                </ScrollArea>
                <div className="border-t p-3 bg-card">
                  <div className="flex gap-2">
                    <Input value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); onAsk() }}} placeholder={doc?.status==="ready" ? "Ask about your file..." : "Upload a file to chat"} disabled={!doc || doc.status!=="ready" || chat.isPending} className="flex-1" />
                    <Button onClick={onAsk} disabled={!question.trim() || !doc || doc.status!=="ready" || chat.isPending} className="gap-2">{chat.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}Send</Button>
                  </div>
                  <p className="text-xs text-muted-foreground text-center mt-2">Guest chats are isolated · Auto-deletes in {formatTTL(expiresIn)} · <Link to="/register" className="text-primary hover:underline">Sign up to keep files</Link></p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
