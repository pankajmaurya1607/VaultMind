import { useEffect, useState, useCallback, createContext, useContext } from "react"

interface Toast {
  id: number
  message: string
  type: "success" | "error"
}

interface ToastCtx {
  toast: (message: string, type?: "success" | "error") => void
}

const ToastContext = createContext<ToastCtx>({ toast: () => {} })

export function useToast() {
  return useContext(ToastContext)
}

let nextId = 0

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const add = useCallback((message: string, type: "success" | "error" = "success") => {
    const id = ++nextId
    setToasts((prev) => [...prev, { id, message, type }])
  }, [])

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toast: add }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDone={remove} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function ToastItem({ toast, onDone }: { toast: Toast; onDone: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDone(toast.id), 3500)
    return () => clearTimeout(timer)
  }, [toast.id, onDone])

  return (
    <div
      className={`px-4 py-3 rounded-xl shadow-lg text-sm font-medium animate-slide-in cursor-pointer max-w-xs ${
        toast.type === "success"
          ? "bg-accent text-white"
          : "bg-error text-white"
      }`}
      onClick={() => onDone(toast.id)}
    >
      {toast.message}
    </div>
  )
}
