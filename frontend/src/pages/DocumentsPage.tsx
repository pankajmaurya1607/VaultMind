import { useState, useMemo } from "react"
import { useDocuments, useDeleteDocument, useDocument } from "@/hooks/useDocuments"
import { useDepartments } from "@/hooks/useReferences"
import { useAuth, isAdmin } from "@/context/AuthContext"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"
import { Upload, Search, FileText, Trash2, Loader2, File, Clock, Hash, ChevronLeft, ChevronRight, Building2 } from "lucide-react"
import UploadDialog from "@/components/documents/UploadDialog"

const statusVariant: Record<string, "success" | "secondary" | "default" | "destructive"> = {
  ready: "success",
  pending: "secondary",
  processing: "default",
  failed: "destructive",
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}
function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit",
  })
}

export default function DocumentsPage() {
  const [page, setPage] = useState(0)
  const [limit, setLimit] = useState(10)
  const skip = page * limit
  const { data: documents, isLoading, error } = useDocuments(5000, { skip, limit })
  const { data: departments } = useDepartments()
  const deptMap = useMemo(() => new Map((departments || []).map((d) => [d.id, d.name])), [departments])
  const deleteDoc = useDeleteDocument()
  const { user } = useAuth()
  const admin = isAdmin(user)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [search, setSearch] = useState("")
  const [detailId, setDetailId] = useState<number | null>(null)
  const { data: detail, isFetching: detailFetching } = useDocument(detailId)

  const filtered = useMemo(() => {
    if (!documents) return []
    if (!search.trim()) return documents
    const q = search.toLowerCase()
    return documents.filter((d) => d.original_filename.toLowerCase().includes(q) || (deptMap.get(d.department_id || 0) || "").toLowerCase().includes(q))
  }, [documents, search, deptMap])

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`Delete "${name}"? This cannot be undone.`)) return
    try {
      await deleteDoc.mutateAsync(id)
      toast.success("Document deleted")
    } catch {
      toast.error("Failed to delete document")
    }
  }

  const listDoc = detailId !== null ? documents?.find((d) => d.id === detailId) : undefined
  const doc = detail ?? listDoc
  const hasMore = documents ? documents.length === limit : false
  const canPrev = page > 0

  return (
    <div className="mx-auto max-w-6xl p-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
          <p className="text-sm text-muted-foreground">
            {documents ? `${documents.length} on page ${page + 1}` : "Loading..."}
            {search && filtered.length !== documents?.length && ` · ${filtered.length} filtered`}
            {documents?.some((d) => d.status === "pending" || d.status === "processing") && (
              <span className="ml-2 inline-flex items-center gap-1 text-primary">
                <Loader2 className="h-3 w-3 animate-spin" /> processing...
              </span>
            )}
          </p>
        </div>
        <Button onClick={() => setUploadOpen(true)} className="gap-2">
          <Upload className="h-4 w-4" />
          Upload
        </Button>
      </div>

      <Card className="mt-6">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(0)
                }}
                placeholder="Filter by filename or department..."
                className="pl-9"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground hidden sm:inline">Rows:</span>
              <Select value={String(limit)} onValueChange={(v) => { setLimit(Number(v)); setPage(0) }}>
                <SelectTrigger className="w-[80px] h-8" aria-label="Rows per page">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="25">25</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading && (
            <div className="p-6 space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}

          {error && (
            <div className="mx-6 my-4 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              Failed to load documents
            </div>
          )}

          {!isLoading && !error && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="rounded-full bg-muted p-4 mb-3">
                <FileText className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium">{search ? "No documents match your filter." : "No documents yet"}</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                {search ? "Try a different filename or department." : "Upload your first document to get started."}
              </p>
              {!search && (
                <Button variant="outline" className="mt-4 gap-2" onClick={() => setUploadOpen(true)}>
                  <Upload className="h-4 w-4" /> Upload document
                </Button>
              )}
            </div>
          )}

          {filtered.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Dept</TableHead>
                      <TableHead>Chunks</TableHead>
                      <TableHead>Uploaded</TableHead>
                      {admin && <TableHead className="text-right">Actions</TableHead>}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filtered.map((d) => (
                      <TableRow
                        key={d.id}
                        className="cursor-pointer"
                        onClick={() => setDetailId(d.id)}
                      >
                        <TableCell className="font-medium max-w-[240px]">
                          <div className="flex items-center gap-2 truncate">
                            <File className="h-4 w-4 text-muted-foreground shrink-0" />
                            <span className="truncate" title={d.original_filename}>{d.original_filename}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">{d.mime_type || "—"}</TableCell>
                        <TableCell className="text-muted-foreground whitespace-nowrap text-xs">{formatSize(d.file_size)}</TableCell>
                        <TableCell>
                          <Badge variant={statusVariant[d.status] || "secondary"} className="capitalize text-xs">
                            {d.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs">
                          <span className="inline-flex items-center gap-1 text-muted-foreground">
                            <Building2 className="h-3 w-3" /> {d.department_id ? (deptMap.get(d.department_id) || `#${d.department_id}`) : "—"}
                          </span>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">{d.chunk_count}</TableCell>
                        <TableCell className="text-muted-foreground whitespace-nowrap text-xs">{formatDate(d.created_at)}</TableCell>
                        {admin && (
                          <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(d.id, d.original_filename)}
                              disabled={deleteDoc.isPending}
                              className="h-7 text-muted-foreground hover:text-destructive"
                              aria-label={`Delete ${d.original_filename}`}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="flex items-center justify-between border-t px-4 py-3">
                <span className="text-xs text-muted-foreground">
                  Page {page + 1} · {filtered.length} items {search && `(filtered)`}
                </span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled={!canPrev} onClick={() => setPage((p) => Math.max(0, p - 1))} className="h-8 gap-1">
                    <ChevronLeft className="h-4 w-4" /> Prev
                  </Button>
                  <Button variant="outline" size="sm" disabled={!hasMore && filtered.length <= limit} onClick={() => setPage((p) => p + 1)} className="h-8 gap-1">
                    Next <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <UploadDialog open={uploadOpen} onOpenChange={setUploadOpen} />

      <Dialog open={detailId !== null} onOpenChange={(o) => !o && setDetailId(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="truncate pr-6">{doc?.original_filename || "Document details"}</DialogTitle>
            <DialogDescription>Detailed info about the selected document.</DialogDescription>
          </DialogHeader>

          {!doc ? (
            <div className="space-y-3 py-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          ) : (
            <div className="space-y-4 py-2">
              {detailFetching && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" /> Refreshing...
                </div>
              )}
              <div className="grid gap-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" /> Status</span>
                  <Badge variant={statusVariant[doc.status] || "secondary"} className="capitalize">{doc.status}</Badge>
                </div>
                <Separator />
                <Row label="Size" value={formatSize(doc.file_size)} icon={File} />
                <Row label="MIME type" value={doc.mime_type || "—"} icon={FileText} />
                <Row label="Department" value={doc.department_id ? (deptMap.get(doc.department_id) || String(doc.department_id)) : "—"} icon={Building2} />
                <Row label="Chunks" value={String(doc.chunk_count)} icon={Hash} />
                <Row label="Uploaded" value={formatDateTime(doc.created_at)} icon={Clock} />
                <Row label="Owner ID" value={String(doc.uploaded_by)} icon={Hash} />
                {doc.error_message && (
                  <>
                    <Separator />
                    <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                      {doc.error_message}
                    </div>
                  </>
                )}
                {(doc.status === "pending" || doc.status === "processing") && (
                  <p className="text-xs text-muted-foreground">Document is still processing. It will refresh automatically.</p>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

function Row({ label, value, icon: Icon }: { label: string; value: string; icon?: React.ElementType }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-muted-foreground flex items-center gap-1.5">
        {Icon && <Icon className="h-3.5 w-3.5" />}
        {label}
      </span>
      <span className="font-medium truncate text-right">{value}</span>
    </div>
  )
}
