import { useState, useRef, useEffect } from "react"
import { useChatSessions, useChatMessages, useSendMessage } from "../hooks/useChat"
import type { Chunk, ChatSession } from "../types"

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric", minute: "2-digit",
  })
}

function SourceChips({ sources }: { sources: Chunk[] }) {
  const [open, setOpen] = useState(false)
  if (!sources || sources.length === 0) return null
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-accent hover:text-accent-hover transition-colors"
      >
        {open ? "Hide" : "Show"} sources ({sources.length})
      </button>
      {open && (
        <div className="mt-1.5 space-y-1">
          {sources.map((s, i) => (
            <div key={i} className="text-xs text-text-muted bg-bg-base rounded-lg px-3 py-1.5 border border-border">
              <span className="font-medium text-text-dim">{s.filename}</span>
              <span className="mx-1.5">&middot;</span>
              chunk {s.chunk_index}
              <span className="mx-1.5">&middot;</span>
              <span className="font-mono">{(s.score * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function newSessionItem(): ChatSession {
  return { id: 0, title: "+ New Chat", created_at: "" }
}

export default function ChatPage() {
  const { data: sessions } = useChatSessions()
  const [activeId, setActiveId] = useState<number | null>(null)
  const [input, setInput] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const send = useSendMessage()

  const { data: messages, isLoading: messagesLoading } = useChatMessages(activeId && activeId > 0 ? activeId : null)

  const allSessions = [newSessionItem(), ...(sessions || [])]

  const isNew = activeId === 0 || activeId === null

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, send.data])

  useEffect(() => {
    if (send.data) {
      setActiveId(send.data.session_id)
      setInput("")
    }
  }, [send.data])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || send.isPending) return
    setInput("")
    await send.mutateAsync({
      sessionId: isNew ? null : activeId,
      question: trimmed,
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full animate-fade-in">
      <div className="w-56 border-r border-border bg-bg-surface flex-shrink-0 overflow-y-auto hidden md:block">
        <div className="px-3 py-4 space-y-0.5">
          {allSessions.map((s) => (
            <button
              key={s.id || "new"}
              onClick={() => setActiveId(s.id === 0 ? null : s.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate ${
                (s.id === 0 && isNew) || (s.id > 0 && s.id === activeId)
                  ? "bg-accent/10 text-accent font-medium"
                  : "text-text-muted hover:text-text hover:bg-bg-hover"
              }`}
            >
              {s.id === 0 ? "+ New Chat" : s.title}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        {isNew && !send.data && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center px-6">
              <h2 className="text-lg font-semibold text-text mb-2">Ask anything</h2>
              <p className="text-sm text-text-muted max-w-sm">
                Ask questions about your documents and get answers with source citations.
              </p>
            </div>
          </div>
        )}

        {!isNew && messagesLoading && (
          <div className="flex-1 flex items-center justify-center text-sm text-text-muted">
            Loading messages...
          </div>
        )}

        {((!isNew && messages && messages.length > 0) || send.data) && (
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
            {messages?.map((m) => (
              <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[70%] rounded-xl px-4 py-3 ${
                    m.role === "user"
                      ? "bg-accent text-white"
                      : "bg-bg-surface border border-border text-text"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                  {m.role === "assistant" && (
                    <>
                      {m.sources && m.sources.length > 0 && <SourceChips sources={m.sources} />}
                      {m.confidence_score != null && (
                        <p className="text-xs text-text-dim mt-1">
                          Confidence: {(m.confidence_score * 100).toFixed(0)}%
                        </p>
                      )}
                    </>
                  )}
                  <p className="text-xs opacity-50 mt-1">{formatTime(m.created_at)}</p>
                </div>
              </div>
            ))}

            {send.isPending && (
              <div className="flex justify-start">
                <div className="bg-bg-surface border border-border rounded-xl px-4 py-3 text-text-muted text-sm flex items-center gap-2">
                  <span className="inline-block w-3 h-3 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                  Thinking...
                </div>
              </div>
            )}

            {send.data && (
              <div className="flex justify-start">
                <div className="bg-bg-surface border border-border rounded-xl px-4 py-3 text-text max-w-[70%]">
                  {send.isPending ? (
                    <span className="inline-block w-3 h-3 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
                  ) : (
                    <>
                      <p className="text-sm whitespace-pre-wrap">{send.data.answer}</p>
                      {send.data.sources.length > 0 && <SourceChips sources={send.data.sources} />}
                      <p className="text-xs text-text-dim mt-1">
                        Confidence: {(send.data.confidence_score * 100).toFixed(0)}%
                        {" "}&middot;{" "}
                        {send.data.latency_ms}ms
                      </p>
                    </>
                  )}
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}

        <div className="border-t border-border p-3">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isNew ? "Ask a question..." : "Follow up..."}
              className="flex-1 bg-bg-surface border border-border rounded-lg px-4 py-2.5 text-text placeholder:text-text-dim text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30 transition-colors"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || send.isPending}
              className="px-4 py-2.5 text-sm font-medium text-white bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
