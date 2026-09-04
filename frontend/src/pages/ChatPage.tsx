import { useState, useRef, useEffect } from "react"
import { useChatSessions, useChatMessages, useSendMessage, useRenameChat, useDeleteChat } from "@/hooks/useChat"
import type { Source } from "@/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { toast } from "sonner"
import { Send, Loader2, MessageSquare, Plus, Bot, User, ChevronDown, ChevronUp, Sparkles, MoreHorizontal, Pencil, Trash2 } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
}

function formatAnswer(text: string) {
  const lines = text.split("\n")
  const out: React.ReactNode[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    if (!line.trim()) {
      out.push(<div key={`s-${i}`} className="h-2" />)
      i++
      continue
    }
    // Markdown table: consecutive | ... | lines
    if (line.trim().startsWith("|") && line.includes("|")) {
      const rows: string[][] = []
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const cells = lines[i]
          .split("|")
          .slice(1, -1)
          .map((c) => c.trim())
        // skip separator row |---|---|
        if (cells.every((c) => /^[-:]+$/.test(c.replace(/\s/g, "")))) {
          i++
          continue
        }
        rows.push(cells)
        i++
      }
      if (rows.length > 0) {
        out.push(
          <div key={`tbl-${i}`} className="my-3 overflow-x-auto rounded-lg border">
            <table className="w-full text-xs">
              <thead className="bg-muted/50">
                <tr>
                  {rows[0].map((h, hi) => (
                    <th key={hi} className="px-3 py-2 text-left font-semibold whitespace-nowrap">
                      <span dangerouslySetInnerHTML={{ __html: h.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") }} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(1).map((r, ri) => (
                  <tr key={ri} className={ri % 2 === 0 ? "bg-background" : "bg-muted/20"}>
                    {r.map((c, ci) => (
                      <td key={ci} className="px-3 py-2 align-top leading-relaxed" dangerouslySetInnerHTML={{ __html: c.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\*(.*?)\*/g, "<em>$1</em>") }} />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
      continue
    }
    const isHeading = /^##\s/.test(line.trim()) || (/^\*\*.+\*\*$/.test(line.trim()) && line.trim().length < 100)
    const html = line
      .replace(/^##\s+/, "")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\[(\d+)\]/g, '<span class="inline-flex items-center justify-center rounded bg-primary/10 text-primary text-[10px] px-1 py-0 ml-1">$1</span>')
      .replace(/\[([^\]]+\.(pdf|docx|txt|md))\]/gi, '<span class="inline-flex items-center gap-1 rounded bg-primary/10 text-primary text-[11px] px-1.5 py-0 ml-1">📄 $1</span>')
    if (isHeading) {
      out.push(<p key={i} className="text-sm font-semibold mt-3 mb-1 flex items-center gap-1.5" dangerouslySetInnerHTML={{ __html: html }} />)
    } else {
      const isList = /^(\d+\.|\-|\•)\s/.test(line.trim())
      out.push(
        <p key={i} className={isList ? "text-sm leading-relaxed ml-4 flex gap-2" : "text-sm leading-relaxed"} dangerouslySetInnerHTML={{ __html: isList ? `<span class="text-primary">•</span><span>${html.replace(/^(\d+\.|\-|\•)\s/, "")}</span>` : html }} />
      )
    }
    i++
  }
  return out
}

function SourceBlock({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false)
  if (!sources || sources.length === 0) return null
  const hasScores = sources.some((s) => s.score > 0.01)
  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-2">
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1">
          {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {open ? "Hide" : "Show"} sources ({sources.length})
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-1">
        {sources.map((s, i) => (
          <div key={i} className="rounded-md border bg-muted/50 px-3 py-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="font-medium truncate">{s.filename}</span>
              <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">chunk {s.chunk_index}</Badge>
              {hasScores && <span className="ml-auto font-mono text-[11px] text-muted-foreground">{(s.score * 100).toFixed(0)}%</span>}
            </div>
            <p className="mt-1 line-clamp-2 text-muted-foreground leading-relaxed">{s.text.slice(0, 180)}...</p>
          </div>
        ))}
      </CollapsibleContent>
    </Collapsible>
  )
}

export default function ChatPage() {
  const { data: sessions, isLoading: sessionsLoading, error: sessionsError } = useChatSessions()
  const [activeId, setActiveId] = useState<number | null>(null)
  const [input, setInput] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)
  const send = useSendMessage()
  const renameChat = useRenameChat()
  const deleteChat = useDeleteChat()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editTitle, setEditTitle] = useState("")
  const [deleteId, setDeleteId] = useState<number | null>(null)

  const { data: messages, isLoading: messagesLoading, error: messagesError } = useChatMessages(
    activeId && activeId > 0 ? activeId : null
  )

  const isNew = activeId === 0 || activeId === null
  const [optimistic, setOptimistic] = useState<{ id: number; content: string } | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, send.isPending, send.data, optimistic])

  // clear optimistic once real message appears
  useEffect(() => {
    if (optimistic && messages?.some((m) => m.role === "user" && m.content === optimistic.content)) {
      setOptimistic(null)
    }
  }, [messages, optimistic])

  const pendingAnswer = send.data && send.data.session_id === activeId && send.isSuccess ? send.data : null
  const answerInHistory = pendingAnswer != null && (messages ?? []).some((m) => m.role === "assistant" && m.content === pendingAnswer.answer)
  // Belt-and-braces: backend orders by (created_at, id), but sort here too so a
  // refetch after login can never render an answer above its question.
  const sortedMessages = [...(messages ?? [])].sort((a, b) => a.id - b.id)

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || send.isPending) return
    const tempId = Date.now()
    setOptimistic({ id: tempId, content: trimmed })
    setInput("")
    try {
      const result = await send.mutateAsync({ sessionId: isNew ? null : activeId, question: trimmed })
      setActiveId(result.session_id)
    } catch {
      setOptimistic(null)
      setInput(trimmed)
      toast.error("Failed to send message")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const showEmpty = isNew && (!messages || messages.length === 0) && !send.isPending && !pendingAnswer

  return (
    <div className="flex h-[calc(100vh-3.5rem)] animate-fade-in">
      <div className="hidden w-64 shrink-0 flex-col border-r bg-card md:flex">
        <div className="p-3">
          <Button onClick={() => setActiveId(null)} className="w-full gap-2" variant={isNew ? "default" : "outline"} size="sm">
            <Plus className="h-4 w-4" /> New Chat
          </Button>
        </div>
        <ScrollArea className="flex-1 px-3">
          <div className="space-y-1 pb-4">
            {sessionsLoading && (
              <div className="space-y-2 p-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            )}
            {sessionsError && <p className="px-3 py-2 text-xs text-destructive">Failed to load sessions</p>}
            {sessions?.length === 0 && !sessionsLoading && (
              <p className="px-3 py-4 text-center text-xs text-muted-foreground">No conversations yet</p>
            )}
            {sessions?.map((s) => (
              <div
                key={s.id}
                className={cn(
                  "group flex w-full items-center gap-1 rounded-md px-2 py-1 text-sm transition-colors",
                  s.id === activeId ? "bg-primary text-primary-foreground" : "hover:bg-accent hover:text-accent-foreground text-muted-foreground"
                )}
              >
                <button onClick={() => setActiveId(s.id)} className="flex flex-1 items-center gap-2 truncate px-1 py-1 text-left" title={s.title}>
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate flex-1">{s.title}</span>
                </button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className={cn("h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100", s.id === activeId && "opacity-100 text-primary-foreground hover:bg-primary/20")} onClick={(e) => e.stopPropagation()}>
                      <MoreHorizontal className="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-40">
                    <DropdownMenuItem
                      onClick={() => {
                        setEditingId(s.id)
                        setEditTitle(s.title)
                      }}
                    >
                      <Pencil className="h-3.5 w-3.5" /> Rename
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setDeleteId(s.id)}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <div className="flex flex-1 flex-col min-w-0">
        <div className="flex gap-2 overflow-x-auto border-b bg-card p-2 md:hidden">
          <Button size="sm" variant={isNew ? "default" : "outline"} onClick={() => setActiveId(null)} className="shrink-0">
            <Plus className="h-3 w-3" /> New
          </Button>
          {sessions?.map((s) => (
            <Button key={s.id} size="sm" variant={s.id === activeId ? "default" : "outline"} onClick={() => setActiveId(s.id)} className="shrink-0 max-w-[140px] truncate" title={s.title}>
              {s.title}
            </Button>
          ))}
        </div>

        <div className="flex flex-1 flex-col overflow-hidden">
          {showEmpty ? (
            <>
              <div className="flex flex-1 items-center justify-center p-6">
                <div className="text-center max-w-md">
                  <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <Sparkles className="h-6 w-6 text-primary" />
                  </div>
                  <h2 className="text-lg font-semibold">Ask anything</h2>
                  <p className="mt-2 text-sm text-muted-foreground">Ask questions about your documents and get answers with source citations and confidence scores.</p>
                  <div className="mt-6 grid gap-2 text-left">
                    {["What are the company leave policies?", "Summarize the Q4 financial report", "How do I deploy a new service?"].map((q) => (
                      <button key={q} onClick={() => setInput(q)} className="rounded-lg border p-3 text-left text-sm hover:bg-accent transition-colors">
                        &quot;{q}&quot;
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gradient-to-t from-background via-background to-transparent">
                <div className="mx-auto flex max-w-3xl gap-2 rounded-2xl border bg-card shadow-lg p-2">
                  <Input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Ask a question..." className="flex-1 border-0 shadow-none focus-visible:ring-0" disabled={send.isPending} />
                  <Button onClick={handleSend} disabled={!input.trim() || send.isPending} className="gap-2 rounded-xl shrink-0">
                    {send.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} Send
                  </Button>
                </div>
                <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-muted-foreground">AI can make mistakes. Verify important information.</p>
              </div>
            </>
          ) : (
            <>
              <ScrollArea className="flex-1">
                <div className="mx-auto max-w-3xl space-y-4 p-4">
                  {!isNew && messagesLoading && (
                    <div className="space-y-3">
                      <Skeleton className="h-16 w-3/4" />
                      <Skeleton className="h-20 w-3/4 ml-auto" />
                    </div>
                  )}
                  {!isNew && messagesError && (
                    <Card className="border-destructive/30 bg-destructive/10">
                      <CardContent className="py-3 text-sm text-destructive">Failed to load messages</CardContent>
                    </Card>
                  )}
                  {!isNew && !messagesLoading && !messagesError && (!messages || messages.length === 0) && (
                    <p className="py-12 text-center text-sm text-muted-foreground">No messages yet. Start the conversation below.</p>
                  )}
                    {sortedMessages.map((m) => (
                    <div key={m.id} className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}>
                      {m.role === "assistant" && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Bot className="h-4 w-4" />
                        </div>
                      )}
                      <div className={cn("max-w-[75%] rounded-2xl px-4 py-3", m.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border shadow-sm")}>
                        {m.role === "assistant" ? <div className="space-y-1">{formatAnswer(m.content)}</div> : <p className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</p>}
                        {m.role === "assistant" && (
                          <>
                            {m.sources && m.sources.length > 0 && <SourceBlock sources={m.sources} />}
                            {m.confidence_score != null && m.confidence_score > 0.05 && (
                              <p className="mt-2 text-xs opacity-60">
                                Relevance: {(m.confidence_score * 100).toFixed(0)}%
                                {(m as unknown as { tokens_used?: number }).tokens_used != null && ` · ${(m as unknown as { tokens_used: number }).tokens_used} tokens`}
                                {(m as unknown as { latency_ms?: number }).latency_ms != null && ` · ${(m as unknown as { latency_ms: number }).latency_ms}ms`}
                              </p>
                            )}
                            {m.confidence_score != null && m.confidence_score <= 0.05 && (
                              <p className="mt-2 text-xs opacity-50">Sources: {m.sources?.length ?? 0} · template fallback</p>
                            )}
                          </>
                        )}
                        <p className={cn("mt-1 text-xs", m.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground")}>{formatTime(m.created_at)}</p>
                      </div>
                      {m.role === "user" && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
                          <User className="h-4 w-4" />
                        </div>
                      )}
                    </div>
                  ))}
                  {optimistic && (
                    <div className="flex gap-3 justify-end">
                      <div className="max-w-[75%] rounded-2xl bg-primary text-primary-foreground px-4 py-3">
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">{optimistic.content}</p>
                        <p className="mt-1 text-xs text-primary-foreground/70">Sending...</p>
                      </div>
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
                        <User className="h-4 w-4" />
                      </div>
                    </div>
                  )}
                  {send.isPending && (
                    <div className="flex gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
                        <Bot className="h-4 w-4" />
                      </div>
                      <Card className="border">
                        <CardContent className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
                          <Loader2 className="h-4 w-4 animate-spin" /> Thinking...
                        </CardContent>
                      </Card>
                    </div>
                  )}
                  {send.isError && (
                    <Card className="border-destructive/30 bg-destructive/10 mx-auto max-w-md">
                      <CardContent className="py-3 text-center text-sm text-destructive">Failed to send. Your question was restored — try again.</CardContent>
                    </Card>
                  )}
                  {pendingAnswer && !answerInHistory && (
                    <div className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="max-w-[75%] rounded-2xl border bg-card px-4 py-3 shadow-sm">
                        <div className="space-y-1">{formatAnswer(pendingAnswer.answer)}</div>
                        {pendingAnswer.sources.length > 0 && <SourceBlock sources={pendingAnswer.sources} />}
                        {pendingAnswer.confidence_score > 0.05 ? (
                          <p className="mt-2 text-xs text-muted-foreground">Relevance: {(pendingAnswer.confidence_score * 100).toFixed(0)}% · {pendingAnswer.latency_ms}ms · {pendingAnswer.tokens_used} tokens · {(pendingAnswer as unknown as { model?: string }).model ?? "template"}</p>
                        ) : (
                          <p className="mt-2 text-xs text-muted-foreground">Sources: {pendingAnswer.sources.length} · template fallback</p>
                        )}
                      </div>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </div>
              </ScrollArea>
              <div className="p-4 bg-gradient-to-t from-background via-background to-transparent">
                <div className="mx-auto flex max-w-3xl gap-2 rounded-2xl border bg-card shadow-lg p-2">
                  <Input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder={isNew ? "Ask a question..." : "Follow up..."} className="flex-1 border-0 shadow-none focus-visible:ring-0" disabled={send.isPending} />
                  <Button onClick={handleSend} disabled={!input.trim() || send.isPending} className="gap-2 rounded-xl shrink-0">
                    {send.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} Send
                  </Button>
                </div>
                <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-muted-foreground">AI can make mistakes. Verify important information.</p>
              </div>
            </>
          )}
        </div>
      </div>

      <Dialog open={editingId !== null} onOpenChange={(o) => !o && setEditingId(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rename chat</DialogTitle>
          </DialogHeader>
          <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} placeholder="Chat title" maxLength={80} autoFocus onKeyDown={(e) => e.key === "Enter" && editTitle.trim() && renameChat.mutate({ id: editingId!, title: editTitle.trim() }, { onSuccess: () => setEditingId(null) })} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingId(null)}>Cancel</Button>
            <Button
              onClick={() => renameChat.mutate({ id: editingId!, title: editTitle.trim() }, { onSuccess: () => setEditingId(null) })}
              disabled={!editTitle.trim() || renameChat.isPending}
            >
              {renameChat.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteId !== null} onOpenChange={(o) => !o && setDeleteId(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete chat?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">This will permanently delete this chat and its messages. This cannot be undone.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button
              variant="destructive"
              onClick={() => deleteChat.mutate(deleteId!, { onSuccess: () => { if (activeId === deleteId) setActiveId(null); setDeleteId(null) } })}
              disabled={deleteChat.isPending}
            >
              {deleteChat.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
