import { useState, useRef, useCallback } from "react"
import { useUploadDocument } from "../../hooks/useDocuments"

const ALLOWED = [".pdf", ".docx", ".md", ".csv", ".xlsx", ".txt"]

interface UploadModalProps {
  open: boolean
  onClose: () => void
}

function extractError(err: unknown): string {
  if (err instanceof Error) {
    const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
    return detail || err.message
  }
  return "Upload failed"
}

export default function UploadModal({ open, onClose }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [validationError, setValidationError] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const upload = useUploadDocument()

  const reset = () => { setFile(null); setValidationError(""); upload.reset() }

  const validate = (f: File) => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase()
    if (!ALLOWED.includes(ext)) return `Unsupported format. Allowed: ${ALLOWED.join(", ")}`
    if (f.size > 10 * 1024 * 1024) return "File exceeds 10 MB limit"
    return null
  }

  const handleFile = useCallback((f: File) => {
    const err = validate(f)
    if (err) {
      setFile(null)
      setValidationError(err)
      return
    }
    setValidationError("")
    setFile(f)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleSelect = () => {
    const f = inputRef.current?.files?.[0]
    if (f) handleFile(f)
  }

  const handleUpload = async () => {
    if (!file) return
    setValidationError("")
    try {
      await upload.mutateAsync(file)
      reset()
      onClose()
    } catch { /* error handled by mutation state */ }
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="w-full max-w-md bg-bg-elevated border border-border rounded-xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="text-base font-semibold text-text">Upload Document</h2>
          <button onClick={() => { reset(); onClose() }} className="text-text-dim hover:text-text text-lg leading-none">&times;</button>
        </div>

        <div className="p-5 space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              dragOver ? "border-accent bg-accent/5" : "border-border hover:border-accent/50"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.md,.csv,.xlsx,.txt"
              className="hidden"
              onChange={handleSelect}
            />
            <div className="text-2xl mb-2 text-text-muted">📄</div>
            <p className="text-sm text-text-muted">
              {file ? file.name : "Drop a file here or click to browse"}
            </p>
            <p className="text-xs text-text-dim mt-1">PDF, DOCX, MD, CSV, XLSX, TXT &middot; Max 10 MB</p>
          </div>

          {validationError && (
            <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-2.5 animate-fade-in">
              {validationError}
            </div>
          )}

          {upload.error && (
            <div className="bg-error/10 border border-error/30 text-error text-sm rounded-lg px-4 py-2.5 animate-fade-in">
              {extractError(upload.error)}
            </div>
          )}

          <div className="flex gap-3 justify-end">
            <button
              onClick={() => { reset(); onClose() }}
              className="px-4 py-2 text-sm text-text-muted hover:text-text bg-bg-surface border border-border rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!file || upload.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2"
            >
              {upload.isPending ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Uploading...
                </>
              ) : (
                "Upload"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}