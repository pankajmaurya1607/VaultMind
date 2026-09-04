import { useState, useRef, useCallback } from "react"
import { useUploadDocument } from "@/hooks/useDocuments"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { Upload, FileText, Loader2 } from "lucide-react"

const ALLOWED = [".pdf", ".docx", ".txt", ".md"]

function extractError(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
  if (detail) return detail
  if (err instanceof Error) return err.message
  return "Upload failed"
}

export default function UploadDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [validationError, setValidationError] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const upload = useUploadDocument()

  const reset = () => {
    setFile(null)
    setValidationError("")
    upload.reset()
  }

  const handleClose = (next: boolean) => {
    if (!next) reset()
    onOpenChange(next)
  }

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

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const f = e.dataTransfer.files[0]
      if (f) handleFile(f)
    },
    [handleFile]
  )

  const handleSelect = () => {
    const f = inputRef.current?.files?.[0]
    if (f) handleFile(f)
  }

  const handleUpload = async () => {
    if (!file) return
    setValidationError("")
    try {
      await upload.mutateAsync(file)
      toast.success(`"${file.name}" uploaded`)
      reset()
      onOpenChange(false)
    } catch (e) {
      toast.error(extractError(e))
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>PDF, DOCX, TXT, MD · Max 10 MB</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div
            role="button"
            tabIndex={0}
            aria-label="Upload file: drop here or browse"
            onDragOver={(e) => {
              e.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                inputRef.current?.click()
              }
            }}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
              dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50 hover:bg-accent"
            }`}
          >
            <input ref={inputRef} type="file" accept=".pdf,.docx,.txt,.md" className="hidden" onChange={handleSelect} />
            <div className="rounded-full bg-primary/10 p-3 mb-3">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <p className="text-sm font-medium truncate max-w-[220px]">
              {file ? file.name : "Drop a file here or click to browse"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {file ? `${(file.size / 1024).toFixed(1)} KB` : "PDF, DOCX, TXT, MD"}
            </p>
          </div>

          {validationError && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">{validationError}</div>
          )}
          {upload.error && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">
              {extractError(upload.error)}
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={() => handleClose(false)}>
            Cancel
          </Button>
          <Button onClick={handleUpload} disabled={!file || upload.isPending} className="gap-2">
            {upload.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                Upload
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
