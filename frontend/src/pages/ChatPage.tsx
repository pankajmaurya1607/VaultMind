import { useState, useRef, useEffect } from "react"
import { useChatSessions, useChatMessages, useSendMessage } from "@/hooks/useChat"
import type { Source } from "@/types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"
import { Send, Loader2, MessageSquare, Plus, Bot, User, ChevronDown, ChevronUp, Sparkles } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
}

function SourceBlock({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false)
  if (!sources || sources.length === 0) return null
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
              <span className="ml-auto font-mono text-[11px] text-muted-foreground">{(s.score * 100).toFixed(0)}%</span>
            </div>
            <p className="mt-1 line-clamp-2 text-muted-foreground leading-relaxed">{s.text.slice(0, 160)}...</p>
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

  const { data: messages, isLoading: messagesLoading, error: messagesError } = useChatMessages(
    activeId && activeId > 0 ? activeId : null
  )

  const isNew = activeId === 0 || activeId === null

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, send.isPending, send.data])

  const pendingAnswer = send.data && send.data.session_id === activeId && send.isSuccess ? send.data : null
  const answerInHistory = pendingAnswer != null && (messages ?? []).some((m) => m.role === "assistant" && m.content === pendingAnswer.answer)

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || send.isPending) return
    setInput("")
    try {
      const result = await send.mutateAsync({ sessionId: isNew ? null : activeId, question: trimmed })
      setActiveId(result.session_id)
    } catch {
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
              <button
                key={s.id}
                onClick={() => setActiveId(s.id)}
                className={cn(
                  "flex w-full items-center gap-2 truncate rounded-md px-3 py-2 text-left text-sm transition-colors",
                  s.id === activeId ? "bg-primary text-primary-foreground" : "hover:bg-accent hover:text-accent-foreground text-muted-foreground"
                )}
                title={s.title}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <span className="truncate">{s.title}</span>
              </button>
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
              <div className="border-t bg-card p-3">
                <div className="mx-auto flex max-w-3xl gap-2">
                  <Input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Ask a question..." className="flex-1" disabled={send.isPending} />
                  <Button onClick={handleSend} disabled={!input.trim() || send.isPending} className="gap-2">
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
                  {messages?.map((m) => (
                    <div key={m.id} className={cn("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}>
                      {m.role === "assistant" && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Bot className="h-4 w-4" />
                        </div>
                      )}
                      <div className={cn("max-w-[75%] rounded-2xl px-4 py-3", m.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border shadow-sm")}>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</p>
                        {m.role === "assistant" && (
                          <>
                            {m.sources && m.sources.length > 0 && <SourceBlock sources={m.sources} />}
                            {m.confidence_score != null && (
                              <p className="mt-2 text-xs opacity-60">
                                Confidence: {(m.confidence_score * 100).toFixed(0)}%
                                {m.tokens_used != null && ` · ${m.tokens_used} tokens`}
                                {m.latency_ms != null && ` · ${m.latency_ms}ms`}
                              </p>
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
                        <p className="whitespace-pre-wrap text-sm leading-relaxed">{pendingAnswer.answer}</p>
                        {pendingAnswer.sources.length > 0 && <SourceBlock sources={pendingAnswer.sources} />}
                        <p className="mt-2 text-xs text-muted-foreground">Confidence: {(pendingAnswer.confidence_score * 100).toFixed(0)}% · {pendingAnswer.latency_ms}ms · {pendingAnswer.tokens_used} tokens</p>
                      </div>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </div>
              </ScrollArea>
              <div className="border-t bg-card p-3">
                <div className="mx-auto flex max-w-3xl gap-2">
                  <Input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder={isNew ? "Ask a question..." : "Follow up..."} className="flex-1" disabled={send.isPending} />
                  <Button onClick={handleSend} disabled={!input.trim() || send.isPending} className="gap-2">
                    {send.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} Send
                  </Button>
                </div>
                <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-muted-foreground">AI can make mistakes. Verify important information.</p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
